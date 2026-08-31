"use client";
import { useState } from "react";

function UserInput({
  text,
  setText,
}: {
  text: string;
  setText: (text: string) => void;
}) {
  return (
    <div>
      <label htmlFor="user_description">
        Enter information about the job you're looking for (a description,
        your resume, whatever):
      </label>

      <input
        id="user_description"
        type="text"
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Type here..."
        className="mt-2 w-full bg-white text-black placeholder:text-black"
      />
    </div>
  );
}

export default function Home() {
  const [text, setText] = useState("");

  const handleSubmit = async () => {
    const response = await fetch("http://localhost:8000/api/match", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query_text: text,
      }),
    });

    const data = await response.json();

    console.log(data);
  };

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-5xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w text-5xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Welcome to job_seeker. Let's find you some jobs.
          </h1>

          <UserInput text={text} setText={setText} />

          <button className="bg-white text-black" onClick={handleSubmit}>
            Search for jobs
          </button>
        </div>
      </main>
    </div>
  );
}