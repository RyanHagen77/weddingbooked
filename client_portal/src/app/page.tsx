'use client';

import Image from 'next/image';
import React, { useEffect, useState } from 'react';
import Login from '../components/Login';
import { useAuth } from '../components/AuthContext';
import { Cormorant_Garamond } from 'next/font/google';

const cormorant = Cormorant_Garamond({ subsets: ['latin'], weight: ['400','600','700'] });

/* ========= Types ========= */
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
type NextDueLinkResponse = {
  url?: string;
  amount?: string;   // optional
  due_date?: string; // optional
  label?: string;    // optional
};

/* ========= Assets ========= */
const heroImages = [
  '/client_portal/portal_header_photo1.webp',
  '/client_portal/portal_header_photo2.webp',
  '/client_portal/portal_header_photo3.webp',
  '/client_portal/portal_header_photo4.webp',
  '/client_portal/portal_header_photo5.webp',
];

/* =========================
   Header (sticky, translucent)
========================= */
function TopHeader({
  handleLogout,
  scrollTo,
  onMakePayment,
}: {
  handleLogout: () => void;
  scrollTo: (id: string) => void;
  onMakePayment: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  const items = [
    { id: 'photographers', label: 'Photographers' },
    { id: 'wedding-planning-guide', label: 'Planning Guide' },
    { id: 'Messages', label: 'Messages' },
    { id: 'files', label: 'Files' },
    { id: 'faq', label: 'FAQ' },
    { id: 'payments', label: 'Make a Payment' }, // special-cased below
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/85 backdrop-blur border-b border-neutralsoft-200">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 py-3">
        {/* Mobile layout */}
        <div className="flex flex-col items-center lg:hidden">
          <a href="#" aria-label="Essence Weddings Home" className="inline-flex">
            <Image src="/client_portal/Final_Logo.png" alt="Essence Weddings" width={220} height={72} priority />
          </a>

          <button
            type="button"
            className="mt-3 text-4xl p-3 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(v => !v)}
          >
            ☰
          </button>
        </div>

        {/* Desktop layout */}
        <div className="hidden lg:flex items-center justify-between">
          <a href="#" aria-label="Essence Weddings Home" className="inline-flex">
            <Image src="/client_portal/Final_Logo.png" alt="Essence Weddings" width={220} height={72} priority />
          </a>

          <nav>
            <ul className="flex items-center gap-8 font-ui tracking-wide">
              {items.map(i => (
                <li key={i.id}>
                  {i.id === 'payments' ? (
                    <button
                      type="button"
                      onClick={onMakePayment}
                      className="text-sm font-medium rounded-full px-3 py-1.5 text-white
                                 bg-[#C18A8F] hover:bg-[#B07A80] active:bg-[#A36C71]
                                 border border-[#C18A8F] shadow-sm
                                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40"
                    >
                      {i.label}
                    </button>
                  ) : (
                    <a
                      href={`#${i.id}`}
                      onClick={(e) => { e.preventDefault(); scrollTo(i.id); }}
                      className="relative uppercase text-sm text-neutral-700 hover:text-neutral-950 transition-colors
                                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40 rounded"
                    >
                      {i.label}
                      {/* underline accent uses the same pink */}
                      <span className="absolute left-0 -bottom-1 h-[1px] w-0 bg-[#C18A8F]/70 transition-all duration-200 hover:w-full" />
                    </a>
                  )}
                </li>
              ))}
              <li>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="text-sm text-neutral-700 hover:text-neutral-950 transition-colors
                             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40 rounded"
                >
                  Logout
                </button>
              </li>
            </ul>
          </nav>
        </div>

        {/* Mobile nav dropdown */}
        {menuOpen && (
          <nav className="lg:hidden mt-2 border-t border-neutralsoft-200">
            <ul className="flex flex-col items-center gap-3 py-4 text-base font-ui">
              {items.map(i => (
                <li key={i.id}>
                  {i.id === 'payments' ? (
                    <button
                      type="button"
                      onClick={() => { setMenuOpen(false); onMakePayment(); }}
                      className="w-full rounded px-3 py-2 font-medium text-white
                                 bg-[#C18A8F] hover:bg-[#B07A80] active:bg-[#A36C71]
                                 border border-[#C18A8F] shadow-sm
                                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40"
                    >
                      {i.label}
                    </button>
                  ) : (
                    <a
                      href={`#${i.id}`}
                      onClick={(e) => { e.preventDefault(); setMenuOpen(false); scrollTo(i.id); }}
                      className="uppercase block px-2 py-1
                                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40 rounded"
                    >
                      {i.label}
                    </a>
                  )}
                </li>
              ))}
              <li>
                <button
                  type="button"
                  onClick={() => { setMenuOpen(false); handleLogout(); }}
                  className="px-2 py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C18A8F]/40 rounded"
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

/* ======= 5-Image Strip (wider columns) ======= */
function HeroStrip() {
  return (
    <section className="bg-white">
      <div className="max-w-screen-2xl mx-auto px-2 lg:px-4 py-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {heroImages.map((src, i) => (
            <div key={i} className="relative w-full aspect-[3/4] overflow-hidden rounded">
              <Image
                src={src}
                alt={`Essence gallery ${i + 1}`}
                fill
                className="object-cover object-center"
                sizes="(max-width: 1024px) 33vw, 20vw"
                priority={i < 2}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ========= Page ========= */
export default function Home() {
  const [faqOpen, setFaqOpen] = useState<number | null>(null);
  const [photographers, setPhotographers] = useState<Photographer[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [formSubmitted] = useState<boolean>(false);
  const { isAuthenticated, contractId, logout } = useAuth();

  /* Token expiry */
  useEffect(() => {
    const check = () => {
      const tokenExpiration = localStorage.getItem('token_expiration');
      if (tokenExpiration && Date.now() >= Number(tokenExpiration)) {
        alert('Your session has expired. Please log in again.');
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
      setPhotographers([]); setMessages([]); setDocuments([]); setIsLoading(false);
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
        if (pData.prospect_photographer1) list.push(pData.prospect_photographer1);
        if (pData.prospect_photographer2) list.push(pData.prospect_photographer2);
        if (pData.prospect_photographer3) list.push(pData.prospect_photographer3);
        setPhotographers(list);
        setMessages(mData);
        setDocuments(dData || []);
      })
      .catch(err => console.error('Error fetching data:', err))
      .finally(() => setIsLoading(false));
  }, [isAuthenticated, contractId]);

  /* Post message */
  const handlePostMessage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const content = newMessage.trim();
    if (!content) { alert('Message cannot be empty'); return; }
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
      const data = await resp.json();
      setMessages([data, ...messages]);
      setNewMessage('');
    } catch (err) {
      console.error(err);
      alert('Failed to post message. Please try again.');
    }
  };

  /* Make payment: open soonest-due unpaid link */
  const handleMakePayment = async () => {
    if (!contractId) { alert('Missing contract. Please log in again.'); return; }
    const accessToken = localStorage.getItem('access_token') || '';

    try {
      const resp = await fetch(
        `https://www.weddingbooked.app/payments/api/next-due-link/${contractId}/`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!resp.ok) throw new Error(`Failed to fetch payment link: ${resp.status}`);

      const data: NextDueLinkResponse = await resp.json();

      if (data?.url) {
        window.open(data.url, '_blank', 'noopener,noreferrer');
      } else {
        alert('No unpaid payment is currently due.');
      }
    } catch (err) {
      console.error(err);
      alert('Unable to load the payment link. Please try again.');
    }
  };

  if (!isAuthenticated) return <Login onLogin={() => window.location.reload()} />;

  const handleLogout = () => {
    logout();
    setPhotographers([]); setMessages([]); setDocuments([]);
  };

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <main className={`bg-white text-black font-gothic ${cormorant.className}`}>
      <TopHeader
        scrollTo={scrollTo}
        handleLogout={handleLogout}
        onMakePayment={handleMakePayment}
      />

      <HeroStrip />

      {/* Photographers title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
        <h2 className="px-16 text-5xl font-cormorant tracking-wide">PHOTOGRAPHERS</h2>
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
      </div>

      <section id="photographers" className="scroll-mt-0 py-8 px-0 bg-white"> {/* remove side padding */}
        <div className="w-full mx-auto flex flex-wrap justify-center gap-x-4 gap-y-10">
          {photographers.map((p) => {
            const first = (p.name || 'Photographer').split(' ')[0];
            return (
                <div key={p.id} className="w-[220px]"> {/* narrower card */}
                  <div className="relative overflow-hidden">
                    <Image
                        src={p.profile_picture || '/default-profile.jpg'}
                        alt={p.name || 'Photographer'}
                        width={220}
                        height={320}
                        className="w-[220px] h-[320px] object-cover object-top"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-[#C18A8F]">
                      <p className="text-white text-2xl font-cormorant text-center py-2">
                        {first}
                      </p>
                    </div>
                  </div>

                  <a
                      href={p.website || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-4 inline-flex w-full items-center justify-center rounded-full px-6 py-3 text-white text-xl font-medium bg-[#C18A8F] hover:opacity-95 transition shadow-md"
                  >
                    View my Demo
                  </a>
                </div>
            );
          })}
        </div>
      </section>


      {/* Planning Guide title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
        <h2 className="px-16 text-5xl font-cormorant tracking-wide">WEDDING PLANNING GUIDE</h2>
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
      </div>

      <section id="wedding-planning-guide" className="scroll-mt-0 px-4 md:px-6 pb-24">
        {/* Hero image (centered, narrower like screenshot) */}
        <div className="max-w-5xl mx-auto">
          <div className="relative w-full">
            <Image
                src="/client_portal/portal_wdg_photo.webp"
                alt="Wedding Planning Guide"
                width={1400}
                height={560}
                className="w-full h-auto object-cover rounded"
                priority
            />
          </div>
        </div>

        {/* Two columns */}
        <div className="max-w-5xl mx-auto mt-12 grid grid-cols-1 md:grid-cols-2 gap-16">
          {/* Left */}
          <div className="text-black leading-relaxed">
            <p className="text-[17px] md:text-lg leading-8">
              Please take a moment to complete the Wedding Guide below. It gives our
              team the important details we need to understand your plans, coordinate
              logistics, and ensure everything runs smoothly on your big day! Your
              answers help us prepare with care, so you can enjoy every moment with
              confidence.
            </p>

            {contractId ? (
              <button
                onClick={() =>
                  window.open(`/client_portal/wedding-day-guide/${contractId}`, '_blank')
                }
                className="mt-8 mx-auto block w-[260px] md:w-[320px] rounded-full px-8 py-4 text-white text-2xl font-medium bg-[#C18A8F] hover:opacity-95 transition shadow-md"
              >
                Wedding Day Guide
              </button>
            ) : (
              <span className="mt-8 mx-auto block w-[260px] md:w-[320px] rounded-full px-8 py-4 text-white text-2xl font-medium bg-[#C18A8F]/70 cursor-not-allowed text-center">
                Wedding Day Guide
              </span>
            )}
          </div>

          {/* Right */}
          <div className="text-black leading-relaxed">
            <p className="text-[17px] md:text-lg leading-8">
              Need help planning your timeline? We’ve got you covered. From getting
              ready to the last dance, having a well-planned schedule can make all the
              difference. Click below to read our helpful article on how to structure
              your wedding day for a smooth, stress-free experience.
            </p>

            <a
              href="https://www.essenceweddings.com/wedding-planning"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-8 mx-auto block w-[260px] md:w-[320px] rounded-full px-8 py-4 text-white text-2xl font-medium bg-[#C18A8F] hover:opacity-95 transition shadow-md text-center"
            >
              Timeline Article
            </a>
          </div>
        </div>
      </section>

      {/* Messages title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
        <h2 className="px-16 text-5xl font-cormorant tracking-wide">MESSAGES</h2>
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
      </div>

      {/* Messages Section */}
      <section id="Messages" className="scroll-mt-0 px-4 md:px-6 pb-24">
        <div className="max-w-4xl mx-auto">
          {/* Message list */}
          <div className="bg-gray-100 rounded p-6 min-h-[120px]">
            {messages.length > 0 ? (
              messages.map(note => (
                <div key={note.id} className="border-b border-gray-300 pb-3 mb-3 last:border-none last:pb-0 last:mb-0">
                  <p className="text-sm text-gray-600 italic mb-1">
                    From {note.created_by.username} • {new Date(note.created_at).toLocaleString()}
                  </p>
                  <p className="text-black">{note.content}</p>
                </div>
              ))
            ) : (
              <p className="italic text-gray-600">No contract messages available.</p>
            )}
          </div>

          {/* Message form */}
          <form onSubmit={handlePostMessage} className="mt-6">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Write your message here..."
              rows={3}
              className="w-full p-4 border border-gray-400 rounded focus:outline-none focus:border-lightpink"
            ></textarea>

            <div className="flex justify-end mt-4">
              <button
                type="submit"
                className="bg-[#C18A8F] text-white text-2xl font-medium rounded-full px-8 py-2 hover:opacity-95 transition"
              >
                Send Message
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* Files title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
        <h2 className="px-16 text-5xl font-cormorant tracking-wide">FILES</h2>
        <div className="flex-1">
          <div className="border-t-4 border-[#C18A8F]"></div>
          <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
        </div>
      </div>

      <section id="files" className="scroll-mt-0 px-4 md:px-6 pb-24">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          {/* Left: hero image */}
          <div className="w-full">
            <Image
              src="/client_portal/portal_files_photo.webp"      // put your image in /public/client_portal/files-hero.png
              alt="Files section hero"
              width={800}
              height={600}
              className="w-full h-auto object-cover rounded"
              priority
            />
          </div>

          {/* Right: file pills */}
          <div className="w-full">
            {isLoading ? (
              <p className="text-center md:text-left text-gray-600">Loading documents...</p>
            ) : documents.length > 0 ? (
              <ul className="flex flex-col gap-8">
                {documents.map((doc) => (
                  <li key={doc.id} className="flex">
                    <a
                      href={doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full md:w-[640px] inline-flex items-center rounded-full px-8 py-5 text-white text-xl font-medium bg-[#C18A8F] hover:opacity-95 transition shadow-md"
                      title={doc.name}
                    >
                      <span className="truncate">{doc.name}</span>
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-center md:text-left text-gray-600">No documents available.</p>
            )}
          </div>
        </div>
      </section>

      {/* FAQ (wrap title + content under one anchor) */}
      <section id="faq" className="scroll-mt-0">
        {/* Title row */}
        <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
          <div className="flex-1">
            <div className="border-t-4 border-[#C18A8F]"></div>
            <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
          </div>
          <h2 className="px-16 text-5xl font-cormorant tracking-wide text-center">
            FREQUENTLY ASKED QUESTIONS
          </h2>
          <div className="flex-1">
            <div className="border-t-4 border-[#C18A8F]"></div>
            <div className="border-t-2 border-[#C18A8F] mt-[6px]"></div>
          </div>
        </div>

        {/* Content (used to be <section id="faq" ...>) */}
        <div className="px-4 md:px-6 pb-24 text-black font-albert">
          <div className="max-w-5xl mx-auto">
            {/* ...your existing FAQ accordion code stays the same here... */}
          </div>
        </div>


        <div className="max-w-5xl mx-auto">
          {[1, 2, 3, 4, 5].map((index) => {
            const open = faqOpen === index;
            const question =
              index === 1 ? 'When is my payment due?' :
              index === 2 ? 'How do I pay my balance?' :
              index === 3 ? 'How do I preview and book my photographer?' :
              index === 4 ? 'When can I meet my photographer/videographer?' :
              'What if I have other questions before my wedding?';

            return (
              <div key={index} className="py-6">
                {/* Row: question + chevron */}
                <button
                  onClick={() => setFaqOpen(open ? null : index)}
                  className="w-full flex items-center justify-between text-left"
                  aria-expanded={open}
                  aria-controls={`faq-content-${index}`}
                >
                  <h3 className="text-2xl md:text-[26px] font-semibold font-century">{question}</h3>
                  <svg
                      className={`w-7 h-7 transition-transform ${open ? 'rotate-180' : 'rotate-0'}`}
                    viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                    aria-hidden="true"
                  >
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>

                {/* Dusty-rose divider */}
                <div className="mt-4 border-t-2 border-[#C18A8F]" />

                {/* Answer */}
                <div
                  id={`faq-content-${index}`}
                  className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}
                >
                  <div className="overflow-hidden">
                    <div className="pt-6 text-base md:text-lg leading-relaxed font-century">
                      {index === 1 && (
                          <p>
                            All payments are due 60 days before your wedding.
                            You will receive an invoice from our office which will outline your services and your
                            balance.
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
                            <p>We require deposits to hold your wedding day. Deposits may be paid in any of the options
                              listed above.</p>
                          </div>
                      )}

                      {index === 3 && (
                          <p>
                            Photographer demos are available above to preview. Once you have made a decision, please
                            contact us below.
                            If you do not have a preference for a photographer, Essence can choose one for you.
                          </p>
                      )}

                      {index === 4 && (
                          <p>
                            Essence does not offer a face‑to‑face meeting with your photographer/videographer.
                            They will call you the week of your wedding to go over the details of the day.
                          </p>
                      )}

                      {index === 5 && (
                          <div className="space-y-4">
                            <p>
                              You can send the event coordinator a message in the window below in the Messages section.
                            </p>
                            <p className="text-lg">
                              Need help planning?{' '}
                              <a
                                  href="https://www.essenceweddings.com/wedding-planning"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-goodblue underline hover:text-dark-pistachio"
                              >
                                Click here to read our article on timing for your wedding day
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

      <footer className="bg-grayblue text-black py-6">
        <div className="max-w-4xl mx-auto flex justify-between items-center px-4">
          <div>
            <h3 className="text-xl font-bold">Essence Weddings</h3>
            <p className="text-sm">Creating memorable experiences</p>
          </div>
          <div>
            <p className="text-sm">&copy; {new Date().getFullYear()} Essence Weddings. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </main>
  );
}