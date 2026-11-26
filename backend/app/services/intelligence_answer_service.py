"""Read-only, deterministic evidence answers. No model credentials or paid API required."""
import re

SNAPSHOT_BASIS = 'INFERRED_SNAPSHOT_ELAPSED_DAYS'


def question_scope(question, known_lines=None, known_stands=None):
    upper = question.upper()
    line = re.search(r'\bW(?:RM)?\s*#?\s*([1-9][0-9]*)\b', upper)
    position = re.search(r'\b(?:P(?:OSITION)?\s*|POSITION\s+)(10|[1-9])\b', upper)
    stands = set(re.findall(r'\b((?:10|[1-9])(?:\.[1-9][0-9]*|[A-Z]))\b', upper))
    for code in known_stands or []:
        if re.search(r'\bSTAND\s*[-:#]?\s*' + re.escape(code.upper()) + r'(?![A-Z0-9._-])', upper):
            stands.add(code)
    line_name = 'W' + line.group(1) if line else None
    # Registered topology names take precedence over a W-number inside a name.
    for name in sorted(known_lines or [], key=len, reverse=True):
        if len(name) > 1 and re.search(r'(?<![A-Z0-9])' + re.escape(name.upper()) + r'(?![A-Z0-9])', upper):
            line_name = name
            break
    return line_name, int(position.group(1)) if position else None, stands


def _filter(rows, line, position, stands=None):
    return [row for row in rows if (not line or row.get('line') == line)
            and (position is None or row.get('position') == position)
            and (not stands or row.get('stand') in stands)]


def _label(row):
    return f"{row.get('line')} P{row.get('position')}" + (f" · {row['stand']}" if row.get('stand') else '')


def comparison_rows(insights, kind, line=None, position=None, stands=None):
    measured_key = 'measured_completed_stand_performance' if kind == 'stand' else 'measured_weak_positions'
    historical_key = 'historical_stand_performance' if kind == 'stand' else 'weak_positions'
    measured = _filter(insights.get(measured_key, []), line, position, stands)
    historical = _filter(insights.get(historical_key, []), line, position, stands)
    if any(row.get('evidence') == 'SUFFICIENT' for row in measured) or (measured and not historical):
        normalized = [{**row, 'avg_days': row.get('avg_hours'), 'median_days': row.get('median_hours'),
                       'peer_median_days': row.get('peer_median_hours')} for row in measured]
        return normalized, 'MEASURED_MILL_RUNTIME_HOURS', 'mill-running h'
    return historical, SNAPSHOT_BASIS, 'elapsed d'


def answer_from_evidence(question, insights, history):
    """Keep ongoing comparisons and completed history in separate evidence streams."""
    upper = question.upper()
    known_lines = {row['line'] for row in insights.get('ongoing', []) + insights.get('historical_stand_performance', []) if row.get('line')}
    known_stands = {row['stand'] for row in insights.get('ongoing', []) + insights.get('historical_stand_performance', []) if row.get('stand')}
    line, position, stand_codes = question_scope(question, known_lines, known_stands)
    causal_request = bool(re.search(r'WHY|CAUSE|FAIL|REASON|INVESTIGAT', upper))
    spare_request = bool(re.search(r'SPARE|CONSUM|STOCK', upper))
    evidence = []
    limits = ['Snapshot elapsed days are not measured mill-runtime hours. Ongoing installations are excluded from completed-life averages.',
              'Recorded removal reasons and correlations support inspection priorities, not confirmed root causes.']
    if any(history.get('history_truncated', {}).values()):
        limits.append('Historical analytics is limited to the latest 20,000 imported rows per evidence stream.')
    intent = 'HELP'
    answer = 'Ask: Which stand is currently installed longest? Which stand has better completed life at W1 P7? Which positions are weak? Why should W1 P7 be inspected?'
    current = _filter(insights.get('ongoing', []), line, position, stand_codes)
    cohorts, stand_basis, stand_unit = comparison_rows(insights, 'stand', line, position, stand_codes)
    if spare_request and not (causal_request and line and position is not None):
        intent = 'SPARE_USAGE'
        rows = history.get('top_spares', [])[:5]
        answer = ('Highest recorded historical spare usage: ' + '; '.join(f"{r['spare']} ({r['quantity']})" for r in rows) + '. Use the preparation-stock register for its recorded current balance; usage totals do not establish stock or component life.') if rows else 'No historical spare-use evidence is available. Current stock must come from the preparation-stock register.'
        evidence.extend({'label': row['spare'], 'value': str(row['quantity']), 'basis': 'RECORDED_HISTORICAL_USAGE'} for row in rows)
    elif (re.search(r'LONGEST|LONGER|OLDEST|MAXIMUM|MORE\s+(?:RUNNING\s+)?TIME|MOST\s+(?:RUN|HOUR|TIME)|RUNNING\s+(?:TIME|LONG)', upper)
            and not causal_request and not ('LIFE' in upper and not re.search(r'CURRENT|ONGOING|RUNNING|INSTALLED', upper))):
        intent = 'LONGEST_CURRENT'
        if not current:
            answer = 'No ongoing stand installation matches that scope. Select a recorded line, position or stand code.'
        else:
            wants_measured = bool(re.search(r'ACTUAL|MEASURED|MILL.?RUN', upper))
            complete = [r for r in current if r.get('runtime_complete') and r.get('actual_runtime_hours') is not None]
            measured = max(complete, key=lambda r: r['actual_runtime_hours']) if complete else None
            oldest = max(current, key=lambda r: r.get('elapsed_hours') or 0)
            if wants_measured and measured:
                answer = f"{_label(measured)} has the most measured runtime among the {len(complete)} fully covered ongoing installations: {measured['actual_runtime_hours']:.2f} h."
                if len(complete) != len(current):
                    answer += f" Runtime is incomplete for {len(current)-len(complete)} others, so an overall actual-runtime winner cannot be established."
            elif wants_measured:
                answer = 'The longest actual-running stand cannot be established because no matching ongoing campaign has complete runtime coverage.'
            else:
                answer = f"{_label(oldest)} has the oldest current installation: {oldest['elapsed_hours']:.2f} elapsed calendar h since installation."
                if oldest.get('runtime_complete') and oldest.get('actual_runtime_hours') is not None:
                    answer += f" Its measured mill runtime is {oldest['actual_runtime_hours']:.2f} h."
                else:
                    answer += ' Its actual mill-running hours are unknown or incomplete; elapsed time is not proof of longest actual runtime.'
            evidence.append({'label': _label(oldest), 'value': f"{oldest['elapsed_hours']:.2f} elapsed h", 'basis': 'ONGOING_ELAPSED_CALENDAR_HOURS', 'samples': 1})
            if measured:
                evidence.append({'label': _label(measured), 'value': f"{measured['actual_runtime_hours']:.2f} measured h", 'basis': 'MEASURED_MILL_RUNTIME_HOURS', 'samples': 1})
            limits.append('Do not subtract the scheduled 12-hour monthly PM allowance from history. Runtime requires actual start/stop observations.')
    elif re.search(r'WEAK|WORST|LOW(?:ER)?\s+LIFE|ATTENTION|UNDERPERFORM', upper) and not causal_request:
        intent = 'WEAK_POSITIONS'
        candidates, position_basis, position_unit = comparison_rows(insights, 'position', line, position)
        supported = [r for r in candidates if r.get('evidence') == 'SUFFICIENT' and r.get('vs_peer_pct') is not None and r['vs_peer_pct'] < 0]
        supported.sort(key=lambda r: r['vs_peer_pct'])
        if supported:
            answer = 'Positions with shorter observed completed durations than other lines at the same position: ' + '; '.join(
                f"{_label(r)} median {r['median_days']:.2f} {position_unit}, {r['vs_peer_pct']:.1f}% versus independent peers (n={r['campaigns']}, peer n={r['peer_campaigns']})" for r in supported[:5]) + '. These are inspection candidates, not a failure diagnosis.'
        else:
            answer = 'No weak-position conclusion is supported in this scope. At least 3 completed campaigns for the position and 3 independent peer campaigns from other lines at the same position are required.'
            sparse = sorted(candidates, key=lambda r: r.get('campaigns', 0), reverse=True)[:3]
            if sparse:
                answer += ' Available observations: ' + '; '.join(f"{_label(r)} n={r.get('campaigns', 0)}, peer n={r.get('peer_campaigns', 0)}" for r in sparse) + '.'
        for row in supported[:5]:
            evidence.append({'label': _label(row), 'value': f"median {row['median_days']:.2f} {position_unit}; peer {row['peer_median_days']:.2f} {position_unit}", 'basis': position_basis, 'samples': row['campaigns']})
    elif re.search(r'BEST|BETTER|STRONG|COMPARE|AVERAGE|AVG|LIFE|PERFORM', upper) and not causal_request:
        intent = 'COMPLETED_STAND_COMPARISON'
        supported = [r for r in cohorts if r.get('evidence') == 'SUFFICIENT' and r.get('vs_peer_pct') is not None]
        supported.sort(key=lambda r: r['vs_peer_pct'], reverse=True)
        if supported:
            answer = 'Completed stand performance relative to other stand codes on the same line and position: ' + '; '.join(
                f"{_label(r)} median {r['median_days']:.2f} {stand_unit}, {r['vs_peer_pct']:+.1f}% versus peers (n={r['campaigns']}, peer n={r['peer_campaigns']})" for r in supported[:5]) + '. Positive values mean longer observed duration within that cohort, not a best stand across unlike positions.'
        elif cohorts:
            observed = sorted(cohorts, key=lambda r: (r.get('line', ''), r.get('position', 0), -(r.get('median_days') or 0)))[:5]
            answer = 'There is not enough like-for-like evidence to call one stand better. Recorded completed observations: ' + '; '.join(
                f"{_label(r)} average {r['avg_days']:.2f} {stand_unit}, median {r['median_days']:.2f} {stand_unit} (n={r['campaigns']}, peer n={r['peer_campaigns']})" for r in observed) + '. At least 3 completed campaigns on each side are required for screening.'
        else:
            answer = 'No completed stand-life campaigns match this scope. Current ongoing age cannot be substituted for completed life.'
        for row in (supported or cohorts)[:5]:
            evidence.append({'label': _label(row), 'value': f"average {row['avg_days']:.2f} {stand_unit}; median {row['median_days']:.2f} {stand_unit}; peer n={row['peer_campaigns']}", 'basis': stand_basis, 'samples': row['campaigns']})
    elif re.search(r'WHY|CAUSE|FAIL|REASON|INVESTIGAT', upper):
        intent = 'INVESTIGATION'
        causes = history.get('cause_pareto', [])
        local = history.get('position_investigation')
        if local:
            answer = f"{local['line']} P{local['position']}: {local.get('campaigns', 0)} completed snapshot campaigns."
            local_causes = local.get('causes', [])[:3]
            if local_causes:
                answer += ' Recorded removal reasons: ' + '; '.join(f"{r['cause'].replace('_', ' ').lower()} ({r['count']})" for r in local_causes) + '.'
                evidence.extend({'label': r['cause'].replace('_', ' '), 'value': str(r['count']), 'basis': 'RECORDED_REMOVAL_REASON', 'samples': r['count']} for r in local_causes)
            events = local.get('event_summary', {})
            answer += f" Latest linked campaign-event sample: {events.get('count', 0)} records, {events.get('stoppages', 0)} recorded stoppages, {events.get('downtime_minutes', 0)} min logged stoppage duration."
            answer += ' This does not prove a root cause. Inspect repeated component symptoms, fit/clearance and lubrication records, and actual operating conditions before assigning a cause.'
        elif line or position is not None or stand_codes:
            answer = 'A position-specific root cause cannot be inferred from lifetime alone. Specify both a line and position, for example Investigate W1 P7, to retrieve recorded removal reasons and campaign events. Compare fit/clearance and lubrication records, actual stoppages, product/pass conditions and repeated component observations before assigning a cause.'
        elif causes:
            answer = 'Most frequently recorded historical removal-reason categories: ' + '; '.join(f"{r['cause'].replace('_', ' ').lower()} ({r['count']} records)" for r in causes[:5]) + '. These are operator/history labels, not independently verified failure causes.'
            evidence.extend({'label': r['cause'].replace('_', ' '), 'value': str(r['count']), 'basis': 'RECORDED_REMOVAL_REASON', 'samples': r['count']} for r in causes[:5])
        else:
            answer = 'No removal-reason evidence is available for a causal diagnosis. Record the symptom, affected component, inspection findings, action taken and exact campaign link first.'
        if not history.get('data', {}).get('process_observations'):
            answer += ' No process observations are imported, so casting-speed or emulsion-temperature explanations cannot be tested.'
    return {'answer': answer, 'intent': intent, 'evidence': evidence, 'limitations': limits,
            'provider': 'deterministic', 'as_of': insights.get('as_of')}
