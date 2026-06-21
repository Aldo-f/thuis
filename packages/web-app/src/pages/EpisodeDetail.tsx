import { useParams } from "react-router-dom";

function EpisodeDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-bold text-stone-800">
          Episode &mdash; {id ?? "unknown"}
        </h1>
        <p className="mt-1 text-sm text-stone-400">
          Episode metadata and download options.
        </p>
      </section>

      {/* Metadata placeholder */}
      <div className="rounded-lg border border-stone-200 bg-white p-5">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="font-medium text-stone-500">Title</dt>
          <dd className="text-stone-800">&mdash;</dd>
          <dt className="font-medium text-stone-500">Season</dt>
          <dd className="text-stone-800">&mdash;</dd>
          <dt className="font-medium text-stone-500">Episode</dt>
          <dd className="text-stone-800">&mdash;</dd>
          <dt className="font-medium text-stone-500">Duration</dt>
          <dd className="text-stone-800">&mdash;</dd>
          <dt className="font-medium text-stone-500">Air date</dt>
          <dd className="text-stone-800">&mdash;</dd>
        </dl>
      </div>

      {/* Download button */}
      <button
        type="button"
        className="rounded-lg bg-stone-800 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-stone-700"
      >
        Download Episode
      </button>
    </div>
  );
}

export default EpisodeDetail;
