export function generateStaticParams() {
  return [{ id: "jordan-park" }, { id: "morgan-lee" }, { id: "taylor-kim" }];
}

export default function PMLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
