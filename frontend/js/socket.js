/** Socket.IO real-time client */
let socket = null;
const socketListenersQueue = [];

function initSocket() {
  const token = localStorage.getItem(CONFIG.TOKEN_KEY);
  if (!token) return null;

  if (typeof io === "undefined") {
    // Retry initialization in 50ms if script is still loading
    setTimeout(initSocket, 50);
    return null;
  }

  if (socket) return socket;

  socket = io(CONFIG.SOCKET_URL, {
    query: { token },
    transports: ["websocket"],
  });

  socket.on("connect", () => {
    console.log("Socket connected");
    // Register queued event listeners or execute queued connect callbacks
    while (socketListenersQueue.length > 0) {
      const { event, callback } = socketListenersQueue.shift();
      if (event === "connect") {
        callback();
      } else {
        socket.on(event, callback);
      }
    }
  });

  socket.on("notification", (data) => {
    showToast(data.message || data.title, "info");
    if (typeof onNotification === "function") onNotification(data);
  });

  return socket;
}

function joinConversation(convId) {
  if (!socket) initSocket();
  if (socket && socket.connected) {
    socket.emit("join_conversation", { conversation_id: convId });
  } else {
    // If socket is still initializing, retry after connected
    socketListenersQueue.push({
      event: "connect",
      callback: () => socket.emit("join_conversation", { conversation_id: convId })
    });
  }
}

function sendSocketMessage(convId, content) {
  if (!socket) initSocket();
  if (socket) {
    socket.emit("send_message", { conversation_id: convId, content });
  }
}

function onNewMessage(callback) {
  if (!socket) initSocket();
  if (socket && socket.connected) {
    socket.on("new_message", callback);
  } else {
    socketListenersQueue.push({ event: "new_message", callback });
  }
}

function emitTyping(convId) {
  if (socket) socket.emit("typing", { conversation_id: convId });
}

function emitStopTyping(convId) {
  if (socket) socket.emit("stop_typing", { conversation_id: convId });
}

// Multi-user Student Team Hub real-time events
function joinTeam(teamId) {
  if (!socket) initSocket();
  if (socket && socket.connected) {
    socket.emit("join_team", { team_id: teamId });
  } else {
    socketListenersQueue.push({
      event: "connect",
      callback: () => socket.emit("join_team", { team_id: teamId })
    });
  }
}

function leaveTeam(teamId) {
  if (socket) socket.emit("leave_team", { team_id: teamId });
}

function sendTeamSocketMessage(teamId, message) {
  if (!socket) initSocket();
  if (socket) {
    socket.emit("send_team_message", { team_id: teamId, message });
  }
}

function onNewTeamMessage(callback) {
  if (!socket) initSocket();
  if (socket && socket.connected) {
    socket.on("new_team_message", callback);
  } else {
    socketListenersQueue.push({ event: "new_team_message", callback });
  }
}

function emitTeamTyping(teamId) {
  if (socket) socket.emit("team_typing", { team_id: teamId });
}

function emitTeamStopTyping(teamId) {
  if (socket) socket.emit("team_stop_typing", { team_id: teamId });
}
