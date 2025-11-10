import './globals.css'

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="m-10">
        {children}
      </body>
    </html>
  )
}
