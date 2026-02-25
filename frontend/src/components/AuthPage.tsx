import React from "react";
import { AuthForm } from "@/src/components/ui/sign-in-1";
import { Waves } from "lucide-react";
import { Particles } from "@/src/components/ui/particles";

// Helper components for icons to ensure correct styling
const IconGoogle = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}><title>Google</title><path d="M12.24 10.285V14.4h6.806c-.275 1.765-2.056 5.174-6.806 5.174-4.095 0-7.439-3.386-7.439-7.574s3.344-7.574 7.439-7.574c2.33 0 3.891.989 4.785 1.85l3.25-3.138C18.189 1.186 15.479 0 12.24 0 5.48 0 0 5.48 0 12.24s5.48 12.24 12.24 12.24c6.885 0 11.954-4.823 11.954-12.015 0-.795-.084-1.588-.239-2.356H12.24z" fill="currentColor" /></svg>
);

const IconGithub = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}><title>GitHub</title><path d="M12 0C5.373 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.085 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.91 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12Z" fill="currentColor" /></svg>
);

const IconMail = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}><title>Mail</title><path d="M22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6zm-2 0-8 5-8-5h16zm0 12H4V8l8 5 8-5v10z" fill="currentColor" /></svg>
);

interface AuthPageProps {
  onBack: () => void;
  onSignInSuccess: () => void;
}

/**
 * A demo page to showcase the AuthForm component.
 */
export const AuthPage = ({ onBack, onSignInSuccess }: AuthPageProps) => {

  return (
    <div className="flex min-h-screen w-full overflow-hidden flex-col items-center justify-center bg-black p-4 relative">
      <div className="fixed inset-0 z-0 h-full w-full pointer-events-none">
        <Particles quantity={300} className="absolute inset-0 h-full w-full" color="#ffffff" />
      </div>

      <div className="flex flex-col w-full items-center justify-center origin-center scale-[1.2] relative z-10">
        <div className="mb-8 flex items-center gap-2 cursor-pointer" onClick={onBack}>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-black">
            <Waves className="h-5 w-5" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">Ripple</span>
        </div>
        <AuthForm
          title="Welcome Back"
          description="Enter your credentials to access your account."
          primaryAction={{
            label: "Continue with Google",
            icon: <IconGoogle className="mr-2 h-4 w-4" />,
            onClick: onSignInSuccess,
          }}
          secondaryActions={[
            {
              label: "Continue with Email",
              icon: <IconMail className="mr-2 h-4 w-4" />,
              onClick: onSignInSuccess,
            },
            {
              label: "Continue with Github",
              icon: <IconGithub className="mr-2 h-4 w-4" />,
              onClick: onSignInSuccess,
            },
          ]}
          skipAction={{
            label: "Back to Landing",
            onClick: onBack,
          }}
          footerContent={
            <div className="text-white/40">
              By logging in, you agree to our{" "}
              <u className="cursor-pointer transition-colors hover:text-white">Terms of Service</u>{" "}
              and{" "}
              <u className="cursor-pointer transition-colors hover:text-white">Privacy Policy</u>.
            </div>
          }
        />
      </div>
    </div>
  );
};
