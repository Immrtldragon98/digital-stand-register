import type {Metadata, Viewport} from"next";import OfflineSupport from"@/components/layout/OfflineSupport";import Sidebar from"@/components/layout/Sidebar";import Footer from"@/components/layout/Footer";import"./globals.css";
export const metadata:Metadata={title:"Digital Stand Register",description:"WRM stand operations and reliability assistant"};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" className="dark"><body className="bg-industrial-dark text-slate-100 antialiased"><OfflineSupport/><div className="flex min-h-screen"><Sidebar/><div className="flex-1 flex flex-col min-w-0">{children}<Footer/></div></div></body></html>}
