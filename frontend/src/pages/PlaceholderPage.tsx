export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="panel p-10 text-center max-w-lg mx-auto mt-12">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="text-muted text-sm mt-2">Coming in a later release.</p>
    </div>
  );
}
