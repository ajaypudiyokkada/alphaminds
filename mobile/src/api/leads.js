import client from "./client";

export const submitLead = (payload) =>
  client.post("/leads/", payload).then((r) => r.data);
