import { formatDistanceToNowStrict } from "date-fns";

export function timeAgo(isoString) {
  if (!isoString) return null;
  try {
    return formatDistanceToNowStrict(new Date(isoString), { addSuffix: true });
  } catch {
    return null;
  }
}
