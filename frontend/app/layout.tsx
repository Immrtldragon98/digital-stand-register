import type {Metadata, Viewport} from"next";import OfflineSupport from"@/components/layout/OfflineSupport";import AppShell from"@/components/layout/AppShell";import"./globals.css";
export const metadata:Metadata={title:"Digital Stand Register",description:"WRM stand operations and reliability assistant"};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" className="dark"><body className="bg-industrial-dark text-slate-100 antialiased"><OfflineSupport/><AppShell>{children}</AppShell></body></html>}
