import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import "./style.css";
import HumanPlayerInterface from "./components/HumanPlayer/HumanPlayerInterface";

const root = createRoot(document.getElementById("root"));

document.title = "Monopoly DQN Agent";
// set image favicon
const link = document.createElement("link");
link.rel = "icon";
link.href = "/favicon.png";
document.head.appendChild(link);

root.render(
  <StrictMode>
    <HumanPlayerInterface playerPort={6060} />
  </StrictMode>
);
