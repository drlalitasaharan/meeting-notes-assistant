import { Suspense } from "react";

import PayPalCaptureClient from "./PayPalCaptureClient";

export default function PayPalSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto flex min-h-[70vh] max-w-2xl items-center justify-center px-6 py-16 text-center">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h1 className="text-3xl font-bold tracking-tight text-slate-950">
              Confirming payment
            </h1>
            <p className="mt-4 text-base leading-7 text-slate-600">
              Confirming your PayPal payment with MeetIQ...
            </p>
          </div>
        </div>
      }
    >
      <PayPalCaptureClient />
    </Suspense>
  );
}
