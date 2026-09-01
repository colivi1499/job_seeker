"use client";
import { useState } from "react";
import JobCard from "@/frontend/src/components/JobCard";
import { Job } from "@/frontend/src/types/Job";

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
  const [jobs, setJobs] = useState<Job[] | null>(null);

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
    const matches = data.matches;
    const jobs: Job[] = [];
    for (let i = 0; i < matches.length; i++) {
      jobs.push(matches[i].job)
    }

    console.log(jobs)
    setJobs(jobs)
  };

  return (
    <div className={`flex flex-col flex-1 items-center bg-zinc-50 font-sans dark:bg-black
      ${ jobs ? "justify-start" : "justify-center"}`
    }>
      <main className={`flex flex-1 w-full max-w-5xl flex-col items-center justify-between px-16 bg-white dark:bg-black sm:items-start
        transition-all duration-1000 ${jobs ? "py-8" : "py-32"}`
      }>
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w text-4xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Welcome to job_seeker. Let's find you some jobs.
          </h1>

          <UserInput text={text} setText={setText} />

          <button 
            className="bg-white text-black px-6 py-3 rounded-lg font-medium
             transition-all duration-750
             active:scale-95 active:shadow-none
             transition-colors cursor-pointer shadow-sm
             disabled:bg-gray-400 disabled:text-gray-600
             disabled:cursor-not-allowed disabled:hover:bg-gray-400"
            onClick={handleSubmit}
            disabled={!text}>
            Search for jobs
          </button>
        </div>
        <div className="py-4">
          {jobs && (
            <div className="flex flex-col gap-4">
              {jobs.map((job, index) => (
                <div
                  key={job.id}
                  className="job-card-animate"
                  style={{
                    animationDelay: `${index * 150 + 300}ms`,
                  }}
                >
                  <JobCard job={job} />
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}