import client from "./client";

export const getMe = () => client.get("/athlete/me/").then((r) => r.data);

export const getDashboard = () => client.get("/athlete/dashboard/").then((r) => r.data);

export const getSessions = () => client.get("/athlete/sessions/").then((r) => r.data);

export const getSessionDetail = (id) =>
  client.get(`/athlete/sessions/${id}/`).then((r) => r.data);
