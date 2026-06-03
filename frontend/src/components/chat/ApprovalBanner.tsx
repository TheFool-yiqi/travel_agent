type ApprovalBannerProps = {
  onConfirm: () => void;
  onRequestChanges: () => void;
  disabled?: boolean;
};

export function ApprovalBanner({
  onConfirm,
  onRequestChanges,
  disabled = false,
}: ApprovalBannerProps) {
  return (
    <div className="approval-banner" role="region" aria-label="行程确认">
      <p className="approval-banner-text">行程已生成，请确认或提出修改。</p>
      <div className="approval-banner-actions">
        <button
          type="button"
          className="btn-primary approval-banner-confirm"
          disabled={disabled}
          onClick={onConfirm}
        >
          确认行程
        </button>
        <button
          type="button"
          className="approval-banner-secondary"
          disabled={disabled}
          onClick={onRequestChanges}
        >
          请求修改
        </button>
      </div>
    </div>
  );
}
