import BackendStatus from "@/components/BackendStatus";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-16">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Cite</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          An agentic research assistant where every answer is backed by a source.
        </p>
      </header>
      <section className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="mb-2 font-medium">System status</h2>
        <BackendStatus />
      </section>
    </main>
  );
}
