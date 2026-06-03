import { Plane } from "lucide-react";

export function BackgroundDecor() {
  return (
    <>
      <div className="bg-map-lines" aria-hidden />
      <div className="plane-container" aria-hidden>
        <div className="plane-trail" />
        <Plane className="plane-icon" size={24} strokeWidth={1.5} />
      </div>
    </>
  );
}
