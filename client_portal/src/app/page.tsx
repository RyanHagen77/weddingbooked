'use client';

import Image from 'next/image';
import React, { useEffect, useState } from 'react';
import Login from '../components/Login';
import { useAuth } from '../components/AuthContext';
import { Cormorant_Garamond } from 'next/font/google';

const cormorant = Cormorant_Garamond({ subsets: ['latin'], weight: ['400','600','700'] });

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

const heroImages = [
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',
  '/client_portal/top_5_placeholder.png',

];

/* ========= Header ========= */
function TopHeader({
  scrollTo,
  handleLogout,
}: {
  scrollTo: (id: string) => void;
  handleLogout: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="bg-white border-b border-neutral-200">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 py-4">
        {/* Row 1: centered logo */}
        <div className="flex justify-center">
          <Image
            src="/client_portal/Final_Logo.png"
            alt="Essence Weddings"
            width={260}          /* bigger logo */
            height={90}
            priority
            className="h-auto w-auto object-contain"
          />
        </div>

        {/* Row 2: nav (centered) + hamburger on mobile */}
        <div className="mt-4 flex items-center justify-center">
          {/* Desktop nav */}
          <nav className="hidden lg:block">
            <ul className="flex items-center gap-10 text-2xl font-medium">
              <li><a href="#photographers" className="hover:underline">Photographers</a></li>
              <li><a href="#wedding-planning-guide" className="hover:underline">Planning Guide</a></li>
              <li><a href="#Messages" className="hover:underline">Messages</a></li>
              <li><a href="#files" className="hover:underline">Files</a></li>
              <li><a href="#faq" className="hover:underline">FAQ</a></li>
              <li><button onClick={handleLogout} className="hover:underline">Logout</button></li>
            </ul>
          </nav>

          {/* Mobile hamburger */}
          <button
            className="lg:hidden inline-flex items-center justify-center text-5xl p-2"
            onClick={() => setMenuOpen(v => !v)}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            ☰
          </button>
        </div>

        {/* Mobile dropdown */}
          {menuOpen && (
            <nav className="lg:hidden mt-2 border-t border-neutral-200">
              <ul className="flex flex-col gap-4 py-4 text-lg text-center">
                <li><a href="#photographers" onClick={() => setMenuOpen(false)}>Photographers</a></li>
                <li><a href="#wedding-planning-guide" onClick={() => setMenuOpen(false)}>Planning Guide</a></li>
                <li><a href="#Messages" onClick={() => setMenuOpen(false)}>Messages</a></li>
                <li><a href="#files" onClick={() => setMenuOpen(false)}>Files</a></li>
                <li><a href="#faq" onClick={() => setMenuOpen(false)}>FAQ</a></li>
                <li><button onClick={() => { setMenuOpen(false); handleLogout(); }}>Logout</button></li>
              </ul>
            </nav>
          )}
      </div>
    </header>
  );
}

/* ======= 5‑Image Strip (175x350 each) ======= */
function HeroStrip() {
  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 pb-6">
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 place-items-center">
          {heroImages.map((src, i) => (
            <div key={i} className="relative w-[200px] h-[300px] overflow-hidden rounded">
              <Image
                src={src}
                alt={`Essence gallery ${i + 1}`}
                fill
                className="object-cover"           /* use object-contain if you don’t want any crop */
                sizes="200px"                        /* tells Next the rendered width */
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
      <TopHeader scrollTo={scrollTo} handleLogout={handleLogout} />
      <HeroStrip />

      {/* ======= your existing sections below ======= */}

      {/* Photographers title stays the same */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1">
          <div className="border-t-4 border-lightpink"></div>
          <div className="border-t-2 border-lightpink mt-[6px]"></div>
        </div>
        <h2 className="px-16 text-5xl font-cormorant tracking-wide">PHOTOGRAPHERS</h2>
        <div className="flex-1">
          <div className="border-t-4 border-lightpink"></div>
          <div className="border-t-2 border-lightpink mt-[6px]"></div>
        </div>
      </div>

      <section id="photographers" className="py-8 px-4 md:px-6 bg-white">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10 justify-items-center">
          {photographers.map((p) => (
            <div key={p.id} className="w-[360px]">
              {/* Image + name ribbon */}
              <div className="relative overflow-hidden">
                <Image
                  src={p.profile_picture || '/default-profile.jpg'}
                  alt={p.name || 'Photographer'}
                  width={360}
                  height={480}
                  className="w-[360px] h-[480px] object-cover"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-[#C18A8F] bg-opacity-95">
                  <p className="text-white text-2xl md:text-[28px] font-cormorant text-center py-2">
                    {p.name || 'Photographer'}
                  </p>
                </div>
              </div>

              {/* Big rounded button */}
              <div className="mt-6 flex justify-center">
                <a
                  href={p.website || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center rounded-full px-8 py-3 text-white text-xl font-medium bg-[#C18A8F] hover:opacity-95 transition shadow-md"
                >
                  View my Demo
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>


      {/* FAQ title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
        <h2 className="px-16 text-5xl font-cormorant">FAQ</h2>
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
      </div>

      {/* FAQ section */}
      <section id="faq" className="p-6 text-black font-albert py-24 bg-lightpink bg-dot-grid">
        <div className="divide-y divide-gray-200 max-w-4xl mx-auto">
          {[1,2,3,4,5].map((index) => (
            <div
              key={index}
              onClick={() => setFaqOpen(faqOpen === index ? null : index)}
              className="cursor-pointer py-4 transition duration-500 ease-in-out"
              role="button"
              aria-expanded={faqOpen === index}
              aria-controls={`faq-content-${index}`}
            >
              <h3 className="font-bold text-center">
                {index === 1 ? 'When is my payment due?' :
                 index === 2 ? 'How do I pay my balance?' :
                 index === 3 ? 'How to I preview and book my photographer?' :
                 index === 4 ? 'When can I meet my photographer/videographer?' :
                 'What if I have other questions before my wedding?'}
              </h3>
              <div className={`overflow-hidden transition-[max-height] duration-500 ease-in-out ${faqOpen === index ? 'max-h-96' : 'max-h-0'}`}>
                {index === 1 && (
                  <p className="mt-2 text-center">
                    All payments are due 60 days before your wedding.
                    You will receive an invoice from our office which will outline your services and your balance.
                  </p>
                )}
                {index === 2 && (
                  <div className="mt-2 text-center">
                    <p>There are four ways to pay your balance:</p>
                    <ul className="list-disc list-inside">
                      <li>Online with a credit card (There is a 3% credit/debit card fee)</li>
                      <li>Online with an E-Check (There is a $5 ACH fee)</li>
                      <li>Mail a check payable to Essence Photo and Video (1300 Remington Rd suite B, Schaumburg, IL 60173)</li>
                      <li>Money Order payable to Essence Photo and Video</li>
                      <li>In person with cash at any of our locations by appointment</li>
                    </ul>
                    <p>We require deposits to hold your wedding day. Deposits may be paid in any of the options listed above.</p>
                  </div>
                )}
                {index === 3 && (
                  <p className="mt-2 text-center">
                    Photographer demos are available above to preview. Once you have made a decision, please contact us below.
                    If you do not have a preference for a photographer, Essence can choose one for you.
                  </p>
                )}
                {index === 4 && (
                  <p className="mt-2 text-center">
                    Essence does not offer a face-to-face meeting with your photographer/videographer.
                    They will call you the week of your wedding to go over the details of the day.
                  </p>
                )}
                {index === 5 && (
                  <div className="mt-2 text-center">
                    <p className="mb-4">
                      You can send the event coordinator a message in the window below in the messages section.
                    </p>
                    <p className="text-black font-albert text-lg">
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
          ))}
        </div>
      </section>

      {/* Planning Guide title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
        <h2 className="px-16 text-5xl font-cormorant">Wedding Planning Guide</h2>
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
      </div>

      <section id="wedding-planning-guide" className="text-center py-8 mb-[200px]">
        {contractId ? (
          formSubmitted ? (
            <p className="text-lg text-red-500 font-semibold">
              The Wedding Day Guide has been submitted and can no longer be edited.
            </p>
          ) : (
            <>
              <p className="text-lg text-black font-semibold">
                Please click here to fill out your wedding day guide for your team!
              </p>
              <button
                onClick={() => window.open(`/client_portal/wedding-day-guide/${contractId}`, '_blank')}
                className="mt-4 px-6 py-3 bg-pistachio text-black text-lg font-semibold border-2 border-lightpink rounded hover:bg-opacity-90 transition"
              >
                Open Wedding Day Guide
              </button>
            </>
          )
        ) : (
          <p className="text-lg text-black font-semibold">
            Contract ID not available. Please make sure you are logged in.
          </p>
        )}
      </section>

      {/* Messages title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
        <h2 className="px-16 text-5xl font-cormorant">Messages</h2>
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
      </div>

      <section id="Messages" className="p-6 text-black font-albert py-24 bg-lightpink bg-dot-grid">
        <form onSubmit={handlePostMessage}>
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Write your message here..."
            className="w-full p-2 border border-gray-300 rounded"
            rows={3}
          />
          <button type="submit" className="mt-2 bg-black text-white py-2 px-4 rounded">
            Send Message
          </button>
        </form>

        <h3 className="mt-4 text-xl font-bold">Messages</h3>
        {messages.length > 0 ? (
          messages.map(note => (
            <div key={note.id} className="message mt-2 p-2 border border-gray-300 rounded">
              <p><strong>From:</strong> {note.created_by.username}</p>
              <p><strong>Date:</strong> {new Date(note.created_at).toLocaleString()}</p>
              <p>{note.content}</p>
            </div>
          ))
        ) : (
          <p>No contract messages available.</p>
        )}
      </section>

      {/* Files title */}
      <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
        <h2 className="px-16 text-5xl font-cormorant">Files</h2>
        <div className="flex-1"><div className="border-t-4 border-lightpink"></div><div className="border-t-2 border-lightpink mt-[6px]"></div></div>
      </div>

      <section id="files" className="py-12 px-6 text-black bg-pistachio bg-dot-grid">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isLoading ? (
              <p className="col-span-1 md:col-span-2 text-center text-gray-600">Loading documents...</p>
            ) : documents.length > 0 ? (
              documents.map((doc) => (
                <div key={doc.id} className="bg-white rounded-lg p-4 shadow-lg">
                  <h3 className="font-semibold">{doc.name}</h3>
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-goodblue hover:underline"
                  >
                    {doc.name}
                  </a>
                </div>
              ))
            ) : (
              <p className="col-span-1 md:col-span-2 text-center text-gray-600">No documents available.</p>
            )}
          </div>
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
