import { Compass, Plane, Sparkles } from "lucide-react";

export function WelcomeScreen() {
  return (
    <div className="welcome-screen">
      <div className="welcome-screen-stamp" aria-hidden />
      <Compass className="welcome-screen-icon" strokeWidth={1.5} aria-hidden />
      <h3 className="font-serif-brand welcome-screen-title">开启你的下一段旅程</h3>
      <p className="welcome-screen-text">
        告诉我出发城市、时间和偏好，我会像私人旅行顾问一样帮你规划行程。
      </p>
      <ul className="welcome-screen-hints">
        <li>
          <Plane className="welcome-screen-hint-icon" strokeWidth={1.75} aria-hidden />
          「五一从深圳出发，想带娃去成都玩 4 天」
        </li>
        <li>
          <Sparkles className="welcome-screen-hint-icon" strokeWidth={1.75} aria-hidden />
          「预算 5000，喜欢美食和轻松节奏」
        </li>
      </ul>
    </div>
  );
}
