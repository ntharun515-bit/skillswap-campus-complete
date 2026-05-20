/** Socket.IO real-time client */
let socket = null;

function initSocket() {
  const token = localStorage.getItem(CONFIG.TOKEN_KEY);
  if (!token || typeof io === "undefined") return null;

  if (socket) return socket;

  socket = io(CONFIG.SOCKET_URL, {
    query: { token },
    transports: ["websocket", "polling"],
  });

  socket.on("connect", () => console.log("Socket connected"));
  socket.on("notification", (data) => {
    showToast(data.message || data.title, "info");
    if (typeof onNotification === "function") onNotification(data);
  });

  return socket;
}

function joinConversation(convId) {
  if (!socket) initSocket();
  if (socket) socket.emit("join_conversation", { conversation_id: convId });
}

function sendSocketMessage(convId, content) {
  if (!socket) initSocket();
  if (socket) socket.emit("send_message", { conversation_id: convId, content });
}

function onNewMessage(callback) {
  if (!socket) initSocket();
  if (socket) socket.on("new_message", callback);
}

function emitTyping(convId) {
  if (socket) socket.emit("typing", { conversation_id: convId });
}

function emitStopTyping(convId) {
  if (socket) socket.emit("stop_typing", { conversation_id: convId });
}
