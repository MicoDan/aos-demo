import { APP_NAME, LOGO_URL } from "../brand";

/** height / width of public/logo.png (292 x 320). */
const LOGO_ASPECT = 320 / 292;

/** The application logo. `size` is its width in px. */
export function Logo({ size = 44 }: { size?: number }) {
  return <img className="logo" src={LOGO_URL} alt="Republic of Rwanda coat of arms" width={size} height={Math.round(size * LOGO_ASPECT)} />;
}

/** Logo + application name; used in the sidebar and on the sign-in redirect screen. */
export function Brand({ size = 44 }: { size?: number }) {
  return (
    <div className="brand">
      <Logo size={size} />
      <span className="brand-name">{APP_NAME}</span>
    </div>
  );
}
