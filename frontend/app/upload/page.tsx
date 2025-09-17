"use client";
import { useState } from "react";
import axios from "axios";

export default function UploadPage() {
  const [title, setTitle] = useState("");
  const [meetingId, setMeetingId] = useState<string | null>(null);

  const start = async (file: File) => {
    const form = new FormData();
    form.append("title", title);
    const { data } = await axios.post("http://localhost:8000/v1/meetings/start", form);
    setMeetingId(data.meetingId);
    await axios.put(data.uploadUrl, file, { headers: { "Content-Type": file.type } });
    alert("Uploaded. Now run the transcribe & summarize workers for this meeting in your terminal.");
  };

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold mb-4">Upload a Meeting</h1>
      <input className="border p-2 w-full mb-2" placeholder="Meeting title" value={title} onChange={e=>setTitle(e.target.value)} />
      <input type="file" accept="audio/*,video/*" onChange={(e)=> e.target.files && start(e.target.files[0])}/>
      {meetingId && <p className="mt-4">Meeting ID: {meetingId}</p>}
    </div>
  );
}
