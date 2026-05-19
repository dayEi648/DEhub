/**
 * 扫描线纹理覆盖层
 * 模拟CRT显像管的扫描线效果，固定在整个视口上方
 */
export default function Scanlines() {
  return <div className="scanlines-overlay" aria-hidden="true" />;
}
