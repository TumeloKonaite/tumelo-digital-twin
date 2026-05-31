'use client';

import { ChangeEvent, FormEvent, useState } from 'react';
import { Mail, Phone } from 'lucide-react';

import { API_BASE_URL } from '@/lib/api';

type ContactFormValues = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
};

const INITIAL_VALUES: ContactFormValues = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  subject: '',
  message: '',
};

export default function ContactForm() {
  const [values, setValues] = useState<ContactFormValues>(INITIAL_VALUES);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<{ tone: 'success' | 'error'; message: string } | null>(null);

  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setValues(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) return;

    setIsSubmitting(true);
    setStatus(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: values.firstName,
          last_name: values.lastName,
          email: values.email,
          phone: values.phone,
          subject: values.subject,
          message: values.message,
        }),
      });

      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(payload?.detail ?? 'Unable to send contact request.');
      }

      setValues(INITIAL_VALUES);
      setStatus({
        tone: 'success',
        message: payload?.message ?? 'Contact request submitted successfully.',
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to send contact request.';
      setStatus({
        tone: 'error',
        message,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="mt-8 rounded-3xl border border-slate-200 bg-white/85 p-6 shadow-xl shadow-slate-200/60 backdrop-blur sm:p-8">
      <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr]">
        <div>
          <p className="text-xs font-semibold tracking-[0.2em] text-slate-500 uppercase">
            Contact
          </p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Start the conversation directly.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-6 text-slate-600 sm:text-base">
            Use the form to discuss roles, consulting work, or AI engineering opportunities.
          </p>

          <div className="mt-6 space-y-3">
            <div className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
                <Mail className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900">Best for structured outreach</p>
                <p className="mt-1 text-sm text-slate-600">
                  Include role context, team stage, and the kind of systems you need built.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/70 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500 text-slate-950">
                <Phone className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900">Phone number helps</p>
                <p className="mt-1 text-sm text-slate-600">
                  Add one if you want faster scheduling or callback coordination.
                </p>
              </div>
            </div>
          </div>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">First name</span>
              <input
                required
                name="firstName"
                value={values.firstName}
                onChange={handleChange}
                className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Last name</span>
              <input
                required
                name="lastName"
                value={values.lastName}
                onChange={handleChange}
                className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Email</span>
              <input
                required
                type="email"
                name="email"
                value={values.email}
                onChange={handleChange}
                className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Phone</span>
              <input
                required
                name="phone"
                value={values.phone}
                onChange={handleChange}
                className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </label>
          </div>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Subject</span>
            <input
              required
              name="subject"
              value={values.subject}
              onChange={handleChange}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            />
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Message</span>
            <textarea
              required
              name="message"
              value={values.message}
              onChange={handleChange}
              rows={6}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            />
          </label>

          {status && (
            <div
              className={`rounded-2xl border px-4 py-3 text-sm ${
                status.tone === 'success'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : 'border-rose-200 bg-rose-50 text-rose-800'
              }`}
            >
              {status.message}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? 'Sending...' : 'Send contact request'}
          </button>
        </form>
      </div>
    </section>
  );
}
