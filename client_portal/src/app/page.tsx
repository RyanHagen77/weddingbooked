'use client';

import Image from 'next/image';
import React, { useEffect, useState } from 'react';
import Login from '../components/Login';
import { useAuth } from '../components/AuthContext';

/* =========================
   Types
========================= */
interface Photographer {
  id: string;
  name: string;
  website: string;
  profile_picture: string;
}
interface Message {
  id: string;
  content: string;
  created_by: { username: string };
  created_at: string;
}
interface Document {
  id: string;
  name: string;
  url: string;
}

/* =========================
   Constants (placeholders)
========================= */
const heroImages = [
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
];

/* =========================
   Small UI atoms
========================= */
function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="max-w-6xl mx-auto my-10 px-4 flex items-center gap-6">
      <span className="flex-1 border-t border-neutralsoft-200" />
      <h2 className="px-2 text-3xl md:text-4xl font-heading tracking-wide text-neutral-900 text-center">
        {children}
      </h2>
      <span className="flex-1 border-t border-neutralsoft-200" />
    </div>
  );
}

function PillButtonLink(props: React.AnchorHTMLAttributes<HTMLAnchorElement>) {
  const { className = '', ...rest } = props;
  return (
    <a
      {...rest}
      className={
        `inline-flex items-center justify-center rounded-2xl px-8 py-3
         text-white font-ui text-base md:text-lg bg-rose-300
         transition-all duration-200 hover:opacity-95 hover:-translate-y-0.5 shadow-md
         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200 ${className}`
      }
    />
  );
}

function PillButton(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { className = '', ...rest } = props;
  return (
    <button
      {...rest}
      className={
        `inline-flex items-center justify-center rounded-2xl px-8 py-3
         text-white font-ui text-base md:text-lg bg-rose-300
         transition-all duration-200 hover:opacity-95 hover:-translate-y-0.5 shadow-md
         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200 ${className}`
      }
    />
  );
}

function Notice({ children }: { children: React.ReactNode }) {
  return (
    <div
      role="status"
      className="rounded-2xl border border-rose-200 bg-rose-50 text-neutral-900 px-4 py-3"
    >
      {children}
    </div>
  );
}

/* =========================
   Header (sticky, translucent)
========================= */
function TopHeader({
  handleLogout,
}: {
  handleLogout: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const items = [
    { href: '#photographers', label: 'Photographers' },
    { href: '#wedding-planning-guide', label: 'Planning Guide' },
    { href: '#messages', label: 'Messages' },
    { href: '#files', label: 'Files' },
    { href: '#faq', label: 'FAQ' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/85 backdrop-blur border-b border-neutralsoft-200">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 py-3">
        <div className="flex items-center justify-between">
          <a href="#" aria-label="Essence Weddings Home" className="inline-flex">
            <Image
              src="/client_portal/Final_Logo.png"
              alt="Essence Weddings"
              width={220}
              height={72}
              priority
              className="h-auto w-auto object-contain"
            />
          </a>

          {/* Desktop nav */}
          <nav className="hidden lg:block">
            <ul className="flex items-center gap-8 font-ui tracking-wide">
              {items.map(i => (
                <li key={i.href}>
                  <a
                    href={i.href}
                    className="relative uppercase text-sm text-neutral-700 hover:text-neutral-950 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200 rounded"
                  >
                    {i.label}
                    <span className="absolute left-0 -bottom-1 h-[1px] w-0 bg-rose-200 transition-all duration-200 hover:w-full" />
                  </a>
                </li>
              ))}
              <li>
                <button
                  onClick={handleLogout}
                  className="text-sm text-neutral-700 hover:text-neutral-950 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200 rounded"
                >
                  Logout
                </button>
              </li>
            </ul>
          </nav>

          {/* Mobile */}
          <button
            className="lg:hidden text-3xl p-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(v => !v)}
          >
            ☰
          </button>
        </div>

        {menuOpen && (
          <nav className="lg:hidden mt-2 border-t border-neutralsoft-200">
            <ul className="flex flex-col items-center gap-3 py-4 text-base font-ui">
              {items.map(i => (
                <li key={i.href}>
                  <a
                    href={i.href}
                    onClick={() => setMenuOpen(false)}
                    className="uppercase block px-2 py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200 rounded"
                  >
                    {i.label}
                  </a>
                </li>
              ))}
              <li>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    handleLogout();
                  }}
                  className="px-2 py-1"
                >
                  Logout
                </button>
              </li>
            </ul>
          </nav>
        )}
      </div>
    </header>
  );
}

/* =========================
   Hero Strip (4 images, 2×2 mobile)
========================= */
function HeroStrip() {
  const images = heroImages.slice(0, 4);

  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 pb-6">
        <div className="grid gap-3 sm:gap-4 grid-cols-2 md:grid-cols-4">
          {images.map((src, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl aspect-[7/10]">
              <Image
                src={src}
                alt={`Essence gallery ${i + 1}`}
                fill
                className="object-cover transition-transform duration-300 group-hover:scale-[1.02]"
                sizes="(min-width:1024px) 22vw, (min-width:640px) 30vw, 45vw"
                priority={i === 0}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* =========================
   Page
========================= */
export default function Home() {
  const [faqOpen, setFaqOpen] = useState<number | null>(null);
  const [photographers, setPhotographers] = useState<Photographer[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [banner, setBanner] = useState<string | null>(null);

  const { isAuthenticated, contractId, logout } = useAuth();

  /* Session expiry: inline banner, not alert */
  useEffect(() => {
    const check = () => {
      const tokenExpiration = localStorage.getItem('token_expiration');
      if (tokenExpiration && Date.now() >= Number(tokenExpiration)) {
        setBanner('Your session has expired. Please log in again.');
        logout();
      }
    };
    check();
    const id = setInterval(check, 60 * 1000);
    return () => clearInterval(id);
  }, [logout]);

  /* Fetch data */
  useEffect(() => {
    if (!isAuthenticated || !contractId) {
      setPhotographers([]);
      setMessages([]);
      setDocuments([]);
      setIsLoading(false);
      return;
    }
    const accessToken = localStorage.getItem('access_token') || '';

    const fetchPhotographers = fetch(
      `https://www.weddingbooked.app/bookings/api/prospect-photographers/?contract_id=${contractId}`,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    ).then(r => r.json());

    const fetchMessages = fetch(
      `https://www.weddingbooked.app/communication/api/contract-messages/${contractId}/`,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    ).then(r => r.json());

    const fetchDocuments = fetch(
      `https://www.weddingbooked.app/documents/api/client-documents/${contractId}/`,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    ).then(r => r.json());

    Promise.all([fetchPhotographers, fetchMessages, fetchDocuments])
      .then(([pData, mData, dData]) => {
        const list: Photographer[] = [];
        if (pData?.prospect_photographer1) list.push(pData.prospect_photographer1);
        if (pData?.prospect_photographer2) list.push(pData.prospect_photographer2);
        if (pData?.prospect_photographer3) list.push(pData.prospect_photographer3);
        setPhotographers(list);
        setMessages(Array.isArray(mData) ? mData : []);
        setDocuments(Array.isArray(dData) ? dData : []);
      })
      .catch(err => {
        console.error('Error fetching data:', err);
        setBanner('We couldn’t load some data. Please refresh.');
      })
      .finally(() => setIsLoading(false));
  }, [isAuthenticated, contractId]);

  /* Post message */
  const handlePostMessage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const content = newMessage.trim();
    if (!content) {
      setBanner('Message cannot be empty.');
      return;
    }
    const accessToken = localStorage.getItem('access_token') || '';
    try {
      const resp = await fetch(
        `https://www.weddingbooked.app/communication/api/post-contract-message/${contractId}/`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ content }),
        }
      );
      if (!resp.ok) throw new Error(`Failed to post message: ${resp.status}`);
      const data: Message = await resp.json();
      setMessages(prev => [data, ...(prev ?? [])]);
      setNewMessage('');
    } catch (err) {
      console.error(err);
      setBanner('Failed to post message. Please try again.');
    }
  };

  if (!isAuthenticated) return <Login onLogin={() => window.location.reload()} />;

  const handleLogout = () => {
    logout();
    setPhotographers([]);
    setMessages([]);
    setDocuments([]);
  };

  return (
    <main className="bg-white text-neutral-900 font-body">
      <TopHeader handleLogout={handleLogout} />
      <HeroStrip />

      {/* Inline notice banner */}
      <div className="max-w-5xl mx-auto px-4 mt-4">
        {banner && (
          <div className="mb-4">
            <Notice>{banner}</Notice>
          </div>
        )}
      </div>

      {/* ===================== Photographers ===================== */}
      <SectionTitle>PHOTOGRAPHERS</SectionTitle>

      <section id="photographers" className="py-8 px-4 md:px-6 bg-white scroll-mt-24">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 justify-items-center">
          {photographers.map((p) => (
            <article key={p.id} className="w-[360px]">
              <div className="relative overflow-hidden rounded-2xl">
                <Image
                  src={p.profile_picture || '/default-profile.jpg'}
                  alt={p.name ? `${p.name} portfolio cover` : 'Photographer'}
                  width={360}
                  height={480}
                  className="w-[360px] h-[480px] object-cover"
                />
                <div className="absolute bottom-0 inset-x-0 bg-neutral-900/20 backdrop-blur-sm">
                  <p className="text-white text-xl md:text-2xl font-heading text-center py-2 drop-shadow">
                      {(p.name?.split(' ')[0]) || 'Photographer'}
                  </p>
                </div>
              </div>

              <div className="mt-5 flex justify-center">
                <PillButtonLink
                  href={p.website || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`View demo for ${p.name ?? 'photographer'}`}
                >
                  View Demo
                </PillButtonLink>
              </div>
            </article>
          ))}
          {photographers.length === 0 && (
            <div className="w-full md:w-[360px] text-center text-neutral-600">
              No photographers assigned yet.
            </div>
          )}
        </div>
      </section>

      {/* ===================== Planning Guide ===================== */}
      <SectionTitle>WEDDING PLANNING GUIDE</SectionTitle>

      <section id="wedding-planning-guide" className="scroll-mt-24 px-4 md:px-6 pb-24">
        <div className="max-w-6xl mx-auto">
          <div className="relative w-full overflow-hidden rounded-2xl">
            <Image
              src="/client_portal/wdg-hero.png"
              alt="Wedding Planning Guide"
              width={1600}
              height={600}
              className="w-full h-auto object-cover"
              priority
            />
          </div>
        </div>

        <div className="max-w-6xl mx-auto mt-10 grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="text-black leading-relaxed max-w-[65ch]">
            <p>
              Please take a moment to complete the Wedding Guide below. It gives our team the important
              details we need to understand your plans, coordinate logistics, and ensure everything runs
              smoothly on your big day! Your answers help us prepare with care, so you can enjoy every
              moment with confidence.
            </p>

            {contractId ? (
              <PillButton
                onClick={() =>
                  window.open(`/client_portal/wedding-day-guide/${contractId}`, '_blank')
                }
                className="mt-6"
              >
                Wedding Day Guide
              </PillButton>
            ) : (
              <span className="mt-6 inline-flex items-center justify-center rounded-2xl px-8 py-3 text-white bg-rose-300/70 cursor-not-allowed">
                Wedding Day Guide
              </span>
            )}
          </div>

          <div className="text-black leading-relaxed max-w-[65ch]">
            <p>
              Need help planning your timeline? We’ve got you covered. From getting ready to the last dance,
              having a well‑planned schedule can make all the difference. Click below to read our helpful
              article on how to structure your wedding day for a smooth, stress‑free experience.
            </p>

            <PillButtonLink
              href="https://www.essenceweddings.com/wedding-planning"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6"
            >
              Timeline Article
            </PillButtonLink>
          </div>
        </div>
      </section>

      {/* ===================== Messages ===================== */}
      <SectionTitle>MESSAGES</SectionTitle>

      <section id="messages" className="px-4 md:px-6 pb-24 scroll-mt-24">
        <div className="max-w-4xl mx-auto">
          <div
            role="list"
            aria-label="Contract messages"
            className="bg-neutralsoft-100 rounded-2xl p-6 min-h-[120px]"
          >
            {messages.length > 0 ? (
              messages.map((note) => (
                <div
                  role="listitem"
                  key={note.id}
                  className="border-b border-neutralsoft-200 pb-3 mb-3 last:border-none last:pb-0 last:mb-0"
                >
                  <p className="text-xs text-neutral-600 italic mb-1">
                    From {note.created_by.username} •{' '}
                    {new Date(note.created_at).toLocaleString([], {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </p>
                  <p className="text-neutral-900">{note.content}</p>
                </div>
              ))
            ) : (
              <p className="italic text-neutral-600">No contract messages available.</p>
            )}
          </div>

          <form onSubmit={handlePostMessage} className="mt-6 space-y-3" aria-labelledby="compose-label">
            <label id="compose-label" htmlFor="message" className="sr-only">
              Write your message
            </label>
            <textarea
              id="message"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Write your message…"
              rows={3}
              className="w-full p-4 border border-neutralsoft-200 rounded-2xl
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-200"
            />
            <div className="flex justify-end">
              <PillButton type="submit">Send Message</PillButton>
            </div>
          </form>
        </div>
      </section>

      {/* ===================== Files ===================== */}
      <SectionTitle>FILES</SectionTitle>

      <section id="files" className="scroll-mt-24 px-4 md:px-6 pb-24">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          {/* Left: hero image */}
          <div className="w-full">
            <div className="relative overflow-hidden rounded-2xl">
              <Image
                src="/client_portal/files-hero.png"
                alt="Files section hero"
                width={800}
                height={600}
                className="w-full h-auto object-cover"
                priority
              />
            </div>
          </div>

          {/* Right: file list */}
          <div className="w-full">
            {isLoading ? (
              <ul className="space-y-3">
                {[1,2,3].map(k => (
                  <li key={k} className="rounded-2xl border border-neutralsoft-200 bg-neutralsoft-50 h-[72px] animate-pulse" />
                ))}
              </ul>
            ) : documents.length > 0 ? (
              <ul className="space-y-3">
                {documents.map((doc) => (
                  <li key={doc.id}>
                    <a
                        href={doc.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={doc.name}
                        className="group flex items-center gap-4 rounded-2xl border border-dark-pistachio/30 bg-pistachio/20
             px-4 py-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-soft
             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dark-pistachio/50"
                    >
                      {/* File type badge */}
                      <span
                          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white border border-neutralsoft-200">
                        <span className="font-ui text-xs uppercase tracking-wide text-neutral-700">
                          {doc.name.split('.').pop()?.slice(0, 4) || 'FILE'}
                        </span>
                      </span>

                      {/* Name + meta */}
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-ui text-[15px] text-neutral-900">{doc.name}</p>
                        <p className="text-xs text-neutral-700">View / Download</p>
                      </div>

                      {/* Chevron */}
                      <svg
                          className="h-5 w-5 text-neutral-600 transition-transform group-hover:translate-x-0.5"
                          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"
                      >
                        <path d="M9 18l6-6-6-6"/>
                      </svg>
                    </a>

                  </li>
                ))}
              </ul>
            ) : (
                <div className="rounded-2xl border border-dashed border-neutralsoft-200 p-6 text-neutral-600">
                  No documents yet. Your coordinator will add contracts, invoices, and guides here.
                </div>
            )}
          </div>
        </div>
      </section>

      {/* ===================== FAQ ===================== */}
      <SectionTitle>FREQUENTLY ASKED QUESTIONS</SectionTitle>

      <section id="faq" className="scroll-mt-24 px-4 md:px-6 pb-24 text-neutral-900">
        <div className="max-w-5xl mx-auto">
          {[1, 2, 3, 4, 5].map((index) => {
            const open = faqOpen === index;
            const question =
                index === 1
                    ? 'When is my payment due?'
                    : index === 2
                        ? 'How do I pay my balance?'
                        : index === 3
                            ? 'How do I preview and book my photographer?'
                            : index === 4
                                ? 'When can I meet my photographer/videographer?'
                                : 'What if I have other questions before my wedding?';

            return (
              <div key={index} className="py-6">
                <button
                  onClick={() => setFaqOpen(open ? null : index)}
                  className="w-full flex items-center justify-between text-left"
                  aria-expanded={open}
                  aria-controls={`faq-content-${index}`}
                >
                  <h3 className="text-2xl md:text-[26px] font-heading font-semibold">{question}</h3>
                  <svg
                    className={`w-7 h-7 transition-transform ${open ? 'rotate-180' : 'rotate-0'}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>

                <div className="mt-4 border-t border-neutralsoft-200" />

                <div
                  id={`faq-content-${index}`}
                  className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${
                    open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
                  }`}
                >
                  <div className="overflow-hidden">
                    <div className="pt-6 text-base md:text-lg leading-relaxed font-body">
                      {index === 1 && (
                        <p>
                          All payments are due 60 days before your wedding. You will receive an invoice from our office
                          which will outline your services and your balance.
                        </p>
                      )}

                      {index === 2 && (
                        <div className="space-y-2">
                          <p>There are four ways to pay your balance:</p>
                          <ul className="list-disc list-inside space-y-1">
                            <li>Online with a credit card (There is a 3% credit/debit card fee)</li>
                            <li>Online with an E‑Check (There is a $5 ACH fee)</li>
                            <li>
                              Mail a check payable to Essence Photo and Video (Send to 1300 Remington Rd Suite B,
                              Schaumburg, IL 60173)
                            </li>
                            <li>Money Order payable to Essence Photo and Video (See address above)</li>
                            <li>In person with cash at any of our locations by appointment</li>
                          </ul>
                          <p>
                            We require deposits to hold your wedding day. Deposits may be paid in any of the options
                            listed above.
                          </p>
                        </div>
                      )}

                      {index === 3 && (
                        <p>
                          Photographer demos are available above to preview. Once you have made a decision, please
                          contact us below. If you do not have a preference for a photographer, Essence can choose one
                          for you.
                        </p>
                      )}

                      {index === 4 && (
                        <p>
                          Essence does not offer a face‑to‑face meeting with your photographer/videographer. They will
                          call you the week of your wedding to go over the details of the day.
                        </p>
                      )}

                      {index === 5 && (
                        <div className="space-y-4">
                          <p>You can send the event coordinator a message in the Messages section below.</p>
                          <p className="text-lg">
                            Need help planning?{' '}
                            <a
                              href="https://www.essenceweddings.com/wedding-planning"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="underline text-neutral-900 hover:text-rose-300"
                            >
                              Read our article on timing for your wedding day
                            </a>
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ===================== Footer ===================== */}
      <footer className="bg-neutralsoft-50 text-neutral-900 py-8 border-t border-neutralsoft-200">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 px-4">
          <div>
            <h3 className="text-xl font-heading">Essence Weddings</h3>
            <p className="text-sm text-neutral-600">Creating memorable experiences</p>
          </div>
          <div className="text-sm text-neutral-600">
            &copy; {new Date().getFullYear()} Essence Weddings. All rights reserved.
          </div>
        </div>
      </footer>
    </main>
  );
}
