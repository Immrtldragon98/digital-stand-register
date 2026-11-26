"""Grounded, read-only maintenance answers; no external model or subscription."""
import re
from urllib.parse import urlencode
from app.services.intelligence_answer_service import answer_from_evidence, question_scope


def resolve_scope(question, context, insights):
    rows = insights.get('ongoing', []) + insights.get('historical_stand_performance', [])
    lines = {r['line'] for r in rows if r.get('line')}
    stands = {r['stand'] for r in rows if r.get('stand')}
    line, position, codes = question_scope(question, lines, stands)
    # A new explicit scope replaces the old one. Broad questions clear context.
    broad = bool(re.search(r'\b(ALL LINES|PLANT.WIDE|OVERALL|EVERY LINE|ACROSS LINES)\b', question.upper()))
    if context and re.match(r'^(?:WHAT ABOUT|HOW ABOUT|AND)(?:\s|[?])', question.upper()):
        topic = {'LONGEST_CURRENT': 'Which stand is installed longest?', 'COMPLETED_STAND_COMPARISON': 'Compare completed stand life', 'WEAK_POSITIONS': 'Which positions are weak?', 'INVESTIGATION': 'Investigate recorded reasons', 'RUNTIME_STATUS': 'What is the running state?'} .get(context.get('topic'))
        if topic:
            question = topic + ' ' + question
    if broad:
        return question, None
    if not line and position is None and not codes and context and context.get('line') in lines:
        line, position = context['line'], context.get('position')
        question += f' at {line}' + (f' P{position}' if position is not None else '')
    elif position is not None and not line and context and context.get('line') in lines:
        line = context['line']
        question += f' at {line}'
    return question, {'line': line, 'position': position} if line else None


def duration(hours):
    whole = int(hours)
    return f'{whole // 24}d {whole % 24}h'


def item_matches(question, items):
    """Match registered item-name words; never silently broaden a named stock query."""
    stop = set('what which is are the a an of for me show tell current stock spare spares balance balances available availability quantity quantities do we have how much many any low shortage shortages below minimum life average avg compare please recorded status check list us s all lines plant wide overall'.split())
    question = re.sub(r'\b(?:at|in|on|line|position)\b|\bW(?:RM)?\s*#?\s*\d+\b|\bP\d+\b', ' ', question, flags=re.I)
    words = set(re.findall(r'[a-z0-9]+', question.lower())) - stop
    if not words:
        return items
    return [r for r in items if words & set(re.findall(r'[a-z0-9]+', r['name'].lower()))]


def enhanced_answer(question, insights, history, *, scope=None, plant=None, items=None):
    upper = question.upper()
    answer = answer_from_evidence(question, insights, history)
    answer.update(scope=scope, facts=[], hypotheses=[], missing_evidence=[], next_actions=[], links=[])
    stock_request = bool(re.search(r'\b(STOCK|BALANCE|SHORTAGE|AVAILABLE|AVAILABILITY|QUANTIT(?:Y|IES))\b', upper))
    spare_life = bool(re.search(r'\b(SPARE|COMPONENT|BEARING|SEAL|SLEEVE)S?\b', upper) and re.search(r'\b(LIFE|AVERAGE|AVG)\b', upper))
    runtime_request = bool(re.search(r'\b(UNKNOWN|RUNTIME|RUNNING|STOPPED|STATE)\b', upper)) and not re.search(r'LONGEST|BETTER|WEAK|LIFE|MORE TIME|LONGER|MOST', upper)
    value_request = bool(re.search(r'PREPARATION TIME|PREPARATION TAK|INVESTIGATION (TIME|EFFORT)|SAVINGS|MAINTENANCE VALUE', upper))
    if (stock_request or spare_life) and items is not None and not re.search(r'WHY|CAUSE|FAIL|REASON|INVESTIGAT', upper):
        stock_query = re.sub(re.escape(scope['line']), ' ', question, flags=re.I) if scope else question
        rows = item_matches(stock_query, items)
        answer['intent'] = 'CURRENT_STOCK' if stock_request else 'SPARE_LIFE'
        facts = []
        for row in rows[:12]:
            if stock_request:
                balance = 'Unverified balance' if row['quantity'] is None else f"{row['quantity']} available; minimum {row['minimum']}"
                if row['quantity'] is not None and (row['quantity'] <= 0 or row['quantity'] < row['minimum']):
                    balance += '; stock attention required'
                facts.append({'label': row['name'], 'value': balance, 'basis': 'CURRENT_RECORDED_STOCK'})
            else:
                avg = row.get('average_life_hours')
                source = row.get('average_life_source')
                value = 'Average life not recorded' if avg is None else f'{duration(avg)} average ({avg:g} h)'
                value += f"; {row.get('life_sample_count', 0)} completed units" if source == 'COMPLETED_RECORDS' else '; manual estimate, no completed samples' if source == 'MANUAL' else ''
                facts.append({'label': row['name'], 'value': value, 'basis': source or 'UNKNOWN', 'samples': row.get('life_sample_count', 0)})
        answer['evidence'] = facts
        answer['answer'] = ('Current preparation-stock register: ' if stock_request else 'Recorded spare life: ') + ('; '.join(f"{r['label']}: {r['value']}" for r in facts) if facts else 'No matching registered spare name was found. Use the spare name shown in the stock register.')
        answer['limitations'] = ['Current stock is separate from historical consumption and component life. A recorded balance is not a physical stock verification.']
        if scope:
            answer['limitations'].append('Stock and spare-life evidence is plant-wide; these records do not establish a link to the selected line or position.')
        if len(rows) > 12:
            answer['limitations'].append(f'Showing 12 of {len(rows)} matched items. Narrow the question with a spare name.')
        if any(r['quantity'] is None for r in rows) and stock_request:
            answer['missing_evidence'].append('Unverified balances need a physical count before shortage or purchasing decisions.')
        if spare_life and any(r.get('average_life_source') != 'COMPLETED_RECORDS' for r in rows):
            answer['missing_evidence'].append('Completed component-life samples are missing for some matched spares; manual averages are labelled separately.')
        answer['next_actions'] = ['Check the spare register; record verified stock or completed spare-life evidence.']
        answer['links'] = [{'label': 'Open spares and life records', 'href': '/inventory'}]
    elif runtime_request and plant is not None:
        rows = [r for r in plant['lines'] if not scope or r['name'] == scope['line']]
        facts = [{'label': r['name'], 'value': ('Runtime not recorded' if r['state'] == 'UNKNOWN' else r['state']) + ('; current state needs confirmation' if r['needs_confirmation'] else '; recently confirmed'), 'basis': 'RECORDED_LINE_STATE'} for r in rows]
        answer.update(intent='RUNTIME_STATUS', evidence=facts, answer='; '.join(f"{r['label']}: {r['value']}" for r in facts) or 'No recorded line matches that scope.')
        answer['limitations'] = ['Installed elapsed time includes stoppages. Recording the current state cannot reconstruct earlier running or stopped periods.']
        answer['missing_evidence'] = ['Complete historical start/stop records are required to establish actual campaign runtime.']
        answer['next_actions'] = ['Record each line’s actual current state in Mill runtime, then log state changes when they happen and confirm each shift.']
        answer['links'] = [{'label': 'Record or confirm line state', 'href': '/runtime'}]
    elif value_request and plant is not None:
        observed = plant['observed']
        facts = []
        for label, key, unit in [('Preparation elapsed', 'preparation_hours', 'h'), ('Investigation effort', 'investigation_minutes', 'min')]:
            row = observed[key]
            facts.append({'label': label, 'value': f"{row['average']} {unit} average" if row['average'] is not None else 'Not recorded', 'samples': row['samples'], 'basis': 'OBSERVED_LAST_30_DAYS'})
        answer.update(intent='MAINTENANCE_VALUE', evidence=facts, answer='Last 30 days: ' + '; '.join(f"{r['label']}: {r['value']} ({r['samples']} samples)" for r in facts))
        answer['limitations'] = ['Preparation is elapsed calendar time including pauses; investigation effort is operator-reported. No monetary savings are established by these measurements.']
        if scope:
            answer['limitations'].append('These measurements are plant-wide, not specific to the selected position.')
        answer['next_actions'] = ['Use Start preparation before work and mark Ready when complete; log investigation minutes in Maintenance value.']
        answer['links'] = [{'label': 'View observed outcomes and estimates', 'href': '/value'}]
    else:
        answer['links'] = [{'label': 'Open life comparisons', 'href': '/intelligence'}]
        if answer['intent'] == 'INVESTIGATION':
            local = history.get('position_investigation') or {}
            events = local.get('event_summary', {})
            if not local.get('causes'):
                answer['missing_evidence'].append('No recorded removal reasons for this position.')
            if not events.get('count'):
                answer['missing_evidence'].append('No linked inspection or stoppage events in the returned sample.')
            if not history.get('data', {}).get('process_observations'):
                answer['missing_evidence'].append('No process observations to test operating-condition explanations.')
            answer['hypotheses'] = ['Fit, clearance, lubrication and operating conditions are inspection topics, not diagnosed causes.']
            answer['next_actions'] = ['Inspect the affected component; record the symptom, finding and action against the exact stand campaign.']
        elif answer['intent'] == 'LONGEST_CURRENT':
            answer['next_actions'] = ['Compare actual runtime only for fully covered campaigns; use installed age as elapsed time.']
            if any(not r.get('runtime_complete') for r in insights.get('ongoing', []) if not scope or r['line'] == scope['line']):
                answer['missing_evidence'].append('Some matching current campaigns lack complete runtime history.')
        elif answer['intent'] in ('WEAK_POSITIONS', 'COMPLETED_STAND_COMPARISON'):
            answer['next_actions'] = ['Review completed campaigns and sample counts at comparable positions before choosing a replacement or assigning a cause.']
        elif answer['intent'] == 'HELP':
            answer['answer'] = 'I can explain stand-life evidence, investigate a line and position, check current spare stock and average spare life, explain missing runtime, or summarise preparation and investigation time. Ask one question at a time; I cannot change plant records or diagnose a cause without evidence.'
        if scope and scope.get('position') is not None:
            answer['links'].insert(0, {'label': f"Investigate {scope['line']} P{scope['position']}", 'href': '/investigation?' + urlencode({'line': scope['line'], 'position': scope['position']})})
    answer['facts'] = answer['evidence']
    if scope:
        answer['scope'] = {**scope, 'topic': answer['intent']}
    answer['capability'] = 'Record-based assistant · no generative AI model'
    return answer
