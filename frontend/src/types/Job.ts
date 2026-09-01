export interface Job {
  company: string;
  description: string;
  id: string;
  location: string;
  posted_date: string; // TODO: parse into time?
  skills: [string];
  title: string;
  url: string;
}