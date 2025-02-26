
'use client';

import Image from "next/image";
import React, { useEffect, useState } from 'react';
import Login from '../components/Login';
import { useAuth } from '../components/AuthContext';

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

export default function Home() {
  const [faqOpen, setFaqOpen] = useState<number | null>(null);
  const [photographers, setPhotographers] = useState<Photographer[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [formSubmitted] = useState<boolean>(false);
  const { isAuthenticated, contractId, logout } = useAuth();

  // Check Token Expiration
  useEffect(() => {
    const checkTokenExpiration = () => {
      const tokenExpiration = localStorage.getItem('token_expiration');
      if (tokenExpiration) {
        const now = new Date().getTime();
        if (now >= parseInt(tokenExpiration)) {
          console.log('Token expired, logging out...');
          alert('Your session has expired. Please log in again.');
          logout();
        }
      }
    };

    checkTokenExpiration();

    const interval = setInterval(checkTokenExpiration, 60 * 1000);

    return () => clearInterval(interval);
  }, [logout]);

  // Fetch Data
  useEffect(() => {
    if (isAuthenticated && contractId) {
      const accessToken = localStorage.getItem('access_token');

      const fetchPhotographers = fetch(
        `https://www.enet2.com/bookings/api/prospect-photographers/?contract_id=${contractId}`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      ).then((response) => response.json());

      const fetchMessages = fetch(
        `https://www.enet2.com/communication/api/contract-messages/${contractId}/`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      ).then((response) => response.json());

      const fetchDocuments = fetch(
        `https://www.enet2.com/documents/api/client-documents/${contractId}/`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      ).then((response) => response.json());

      Promise.all([fetchPhotographers, fetchMessages, fetchDocuments])
        .then(([photographersData, messagesData, documentsData]) => {
          const photographersList: Photographer[] = [];
          if (photographersData.prospect_photographer1)
            photographersList.push(photographersData.prospect_photographer1);
          if (photographersData.prospect_photographer2)
            photographersList.push(photographersData.prospect_photographer2);
          if (photographersData.prospect_photographer3)
            photographersList.push(photographersData.prospect_photographer3);

          setPhotographers(photographersList);
          setMessages(messagesData);
          setDocuments(documentsData || []);
        })
        .catch((error) => console.error('Error fetching data:', error))
        .finally(() => setIsLoading(false));
    } else {
      setPhotographers([]);
      setMessages([]);
      setDocuments([]);
      setIsLoading(false);
    }
  }, [isAuthenticated, contractId]);

  const handlePostMessage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (newMessage.trim() === '') {
      alert('Message cannot be empty');
      return;
    }

    const accessToken = localStorage.getItem('access_token');

    try {
      const response = await fetch(
        `https://www.enet2.com/communication/api/post-contract-message/${contractId}/`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content: newMessage }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to post message: ${response.status}`);
      }

      const data = await response.json();
      setMessages([data, ...messages]);
      setNewMessage('');
    } catch (error) {
      console.error('Error posting message:', error);
      alert('Failed to post message. Please try again.');
    }
  };

  if (!isAuthenticated) {
    return <Login onLogin={() => window.location.reload()} />;
  }

  const handleLogout = () => {
    logout();
    setPhotographers([]);
    setMessages([]);
    setDocuments([]);
  };


  return (

      <main className="bg-white">
        <header className="bg-white p-6 text-black md:h-[60vh] relative">
          <div className="max-w-7xl mx-auto flex flex-col justify-center h-full">
            <div className="absolute top-4 right-4">
              <a onClick={handleLogout} className="cursor-pointer text-base sm:text-lg text-black">
                Logout
              </a>
            </div>
            <div className="flex justify-center w-full">
              <div className="relative w-full sm:w-1/2">
                <Image
                    src="/client_portal/Final_Logo.png"  // Correct path for public folder
                    alt="Essense Logo"
                    width={100}
                    height={100}
                    layout="responsive"
                    objectFit="contain"
                    className="sm:w-[400px] sm:h-[400px]"
                />
              </div>
            </div>
            <nav className="mt-6 w-full px-4 pt-8">
              <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
                <div className="bg-black p-2 flex-1 hover:bg-gray-800">
                  <a onClick={() => {
                    const element = document.getElementById('faq');
                    if (element) {
                      element.scrollIntoView({behavior: 'smooth'});
                    }
                  }}
                     className="font-sans font-thin cursor-pointer text-base sm:text-lg text-white block text-center">FAQ</a>
                </div>
                <div className="bg-black p-2 flex-1 hover:bg-gray-800">
                  <a onClick={() => {
                    const element = document.getElementById('photographers');
                    if (element) {
                      element.scrollIntoView({behavior: 'smooth'});
                    }
                  }}
                     className="font-sans font-thin cursor-pointer text-base sm:text-lg text-white block text-center">Photographers</a>
                </div>
                <div className="bg-black p-2 flex-1 hover:bg-gray-800">
                  <a onClick={() => {
                    const element = document.getElementById('wedding-planning-guide');
                    if (element) {
                      element.scrollIntoView({behavior: 'smooth'});
                    }
                  }}
                     className="font-sans font-thin cursor-pointer text-base sm:text-lg text-white block text-center whitespace-nowrap">Wedding
                    Planning Guide</a>
                </div>
                <div className="bg-black p-2 flex-1 hover:bg-gray-800">
                  <a onClick={() => {
                    const element = document.getElementById('Chat');
                    if (element) {
                      element.scrollIntoView({behavior: 'smooth'});
                    }
                  }}
                     className="font-sans font-thin cursor-pointer text-base sm:text-lg text-white block text-center">Chat</a>
                </div>
                <div className="bg-black p-2 flex-1 hover:bg-gray-800">
                  <a onClick={() => {
                    const element = document.getElementById('downloads');
                    if (element) {
                      element.scrollIntoView({behavior: 'smooth'});
                    }
                  }}
                     className="font-sans font-thin cursor-pointer text-base sm:text-lg text-white block text-center">Downloads</a>
                </div>
              </div>
            </nav>
          </div>
        </header>

        <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
          <h2 className="px-16 text-5xl font-brittany">FAQ</h2>
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
        </div>

        <section id="faq" className="p-6 text-black font-albert py-24 bg-lightpink bg-dot-grid">
          <div className="divide-y divide-gray-200 max-w-4xl mx-auto">
            {[1, 2, 3, 4, 5].map((index) => (
                <div
                    key={index}
                    onClick={() => setFaqOpen(faqOpen === index ? null : index)}
                    className="cursor-pointer py-4 transition duration-500 ease-in-out"
                    style={{outline: 'none'}}
                    role="button"
                    aria-expanded={faqOpen === index}
                    aria-controls={`faq-content-${index}`}
                >
                  <h3 className="font-bold text-center ">{
                    index === 1 ? "When is my payment due?" :
                        index === 2 ? "How do I pay my balance?" :
                            index === 3 ? "How to I preview and book my photographer?" :
                                index === 4 ? "When can I meet my photographer/videographer?" :
                                    "What if I have other questions before my wedding?"
                  }</h3>
                  <div
                      className={`overflow-hidden transition-[max-height] duration-500 ease-in-out ${faqOpen === index ? 'max-h-96' : 'max-h-0'}`}
                  >
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
                            <li>Mail a check payable to Essence Photo and Video (Send to 1300 Remington Rd suite B,
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
                        <p className="mt-2 text-center">
                          Photographer demos are available above to preview. Once you have made a decision, please
                          contact us below.
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
                        <p className="mt-2 text-center">
                          You can send the event coordinator a message in the window below in the messages section.
                        </p>
                    )}
                  </div>
                </div>
            ))}
          </div>
        </section>

        <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
          <h2 className="px-16 text-5xl font-brittany">Photographers</h2>
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
        </div>

        <section id="photographers" className="py-6 px-6 bg-pistachio">
          <div className="py-20 max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
            {photographers.map(photographer => (
                <div key={photographer.id}>
                  <div className="text-center bg-white rounded-t-lg shadow-lg block">
                    <a
                        href={photographer.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="transition-transform duration-300 ease-in-out hover:scale-105 block"
                    >
                      {photographer.profile_picture && (
                          <Image
                              src={photographer.profile_picture || '/default-profile.jpg'} // Fallback to a default image
                              alt={photographer.name || 'Photographer'}
                              width={500}
                              height={500}
                              layout="responsive"
                              objectFit="cover"
                          />
                      )}
                    </a>
                  </div>
                  <div className="flex justify-center">
                    <button
                        className="w-[50%] bg-white text-dark-pistachio border-dark-pistachio py-2 my-4 flex justify-center items-center">
                      <a
                          href={photographer.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center"
                      >
                        View My Demo <span className="ml-2 text-lg">&rsaquo;</span>
                      </a>
                    </button>
                  </div>
                </div>
            ))}
          </div>
        </section>

        <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
          <h2 className="px-16 text-5xl font-brittany">Wedding Planning Guide</h2>
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
        </div>
        <section id='wedding-planning-guide' className="text-center py-8 mb-[200px]">
          {contractId ? (
              formSubmitted ? (
                  <p className="text-lg text-red-500 font-semibold">
                    The Wedding Day Guide has been submitted and can no longer be edited.
                  </p>
              ) : (
                  <a
                      href={`/client_portal/wedding-day-guide/${contractId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-lg text-black font-semibold underline"
                  >
                    Please click here to fill out your wedding day guide for your team!
                  </a>
              )
          ) : (
              <p className="text-lg text-black font-semibold">
                Contract ID not available. Please make sure you are logged in.
              </p>
          )}
        </section>
        <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
          <h2 className="px-16 text-5xl font-brittany">Chat</h2>
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
        </div>

        {/* Chat Section */}
        <section id="Chat" className="p-6 text-black font-albert py-24 bg-lightpink bg-dot-grid">
          <form onSubmit={handlePostMessage}>
            <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Write your message here..."
                className="w-full p-2 border border-gray-300 rounded"
                rows={3} // Pass rows as a number
            ></textarea>
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

        <div className="text-black flex items-center justify-center my-8 max-w-[80%] mx-auto">
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
          <h2 className="px-16 text-5xl font-brittany">Downloads</h2>
          <div className="flex-1">
            <div className="border-t-4 border-lightpink"></div>
            <div className="border-t-2 border-lightpink mt-[6px]"></div>
          </div>
        </div>

        <section id="downloads" className="py-12 px-6 text-black bg-pistachio bg-dot-grid">
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {isLoading ? (
                  <p className="col-span-1 md:col-span-2 text-center text-gray-600">
                    Loading documents...
                  </p>
              ) : documents.length > 0 ? (
                  documents.map((doc) => (
                      <div key={doc.id} className="bg-white rounded-lg p-4 shadow-lg">
                        <h3 className="font-semibold">{doc.name}</h3>
                        <a
                            href={`${doc.url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-goodblue hover:underline"
                        >
                          {doc.name}
                        </a>
                      </div>
                  ))
              ) : (
                  <p className="col-span-1 md:col-span-2 text-center text-gray-600">
                    No documents available.
                  </p>
              )}
            </div>
          </div>
        </section>

        <footer className="bg-grayblue text-black py-6">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <div>
              <h3 className="text-xl font-bold">Essence Weddings</h3>
              <p className="text-sm">Creating memorable experiences</p>
            </div>
            <nav>
            </nav>
            <div>
              <p className="text-sm">&copy; {new Date().getFullYear()} Essence Weddings. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </main>
  );
}
