import { Job } from "@/frontend/src/types/Job";

interface JobCardProps {
  job: Job;
}

export default function JobCard({ job }: JobCardProps) {
  const shortDescription =
    job.description.length > 400
      ? `${job.description.slice(0, 400)}...`
      : job.description;
  return (
    <div className="rounded-lg border border-gray-300 bg-white p-6 shadow-md">
      <h2 className="text-xl font-bold text-gray-800">{job.title}</h2>

      <p className="text-gray-600">
        {job.company}
      </p>

      <p className="text-gray-500">
        {job.location}
      </p>

      {job.description && (
        <p className="mt-4 text-gray-700">
          {shortDescription}
        </p>
      )}

      {job.url && (
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-block text-blue-600 hover:underline"
        >
          Apply →
        </a>
      )}
    </div>
  );
}