"use client";
import useSWR from "swr";
const fetcher = (url:string)=>fetch(url).then(r=>r.json());

export default function Page({ params }: { params: { id: string } }) {
  const { data } = useSWR(`http://localhost:8000/v1/meetings/${params.id}`, fetcher, { refreshInterval: 2000 });
  if (!data) return <div className="p-8">Loading…</div>;
  const { meeting, transcript, summary, slides } = data;
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">{meeting?.title || "Meeting"}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section>
          <h2 className="font-semibold mb-2">Summary</h2>
          <pre className="p-3 bg-gray-100 rounded">{summary ? JSON.stringify(summary, null, 2) : "Processing…"}</pre>
        </section>
        <section>
          <h2 className="font-semibold mb-2">Transcript</h2>
          <div className="p-3 bg-gray-100 rounded h-80 overflow-auto whitespace-pre-wrap">
            {transcript?.text || "Processing…"}
          </div>
        </section>
      </div>
      <section>
        <h2 className="font-semibold mb-2">Slides (OCR)</h2>
        <ul className="space-y-2">
          {slides?.map((s:any)=>(
            <li key={s.page} className="p-3 border rounded">
              <div className="text-sm text-gray-500">Page {s.page}</div>
              <div className="whitespace-pre-wrap">{s.ocr_text}</div>
            </li>
          )) || "None"}
        </ul>
      </section>
    </div>
  );
}
