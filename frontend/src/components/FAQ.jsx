/* FAQ — accordion section with common questions */
import React, { useState } from 'react'

const QUESTIONS = [
  {
    q: 'Is my file stored or shared?',
    a: 'No. Files are analysed and deleted from our servers immediately. We never store, share, or use your uploaded content for any purpose.',
  },
  {
    q: 'How accurate is it?',
    a: "Our tool is accurate in most cases but no detector is perfect. Treat results as a guide rather than a final verdict. If you're unsure, ask someone you trust before acting.",
  },
  {
    q: 'What kinds of fakes can it detect?',
    a: "It can detect AI-generated images, deepfake videos, face swaps, and photos manipulated by AI tools. It works best on images and videos of people's faces.",
  },
  {
    q: 'What should I do if something is flagged as fake?',
    a: "Don't share it. Don't send money, personal information, or login details based on it. If you think it's part of a scam, report it to Action Fraud at actionfraud.police.uk or call 0300 123 2040.",
  },
  {
    q: 'Can it analyse videos from WhatsApp or Facebook?',
    a: 'Yes, if you save the video to your device first. On WhatsApp, press and hold the video, tap the share icon, and save it. Then upload the saved file here.',
  },
  {
    q: 'Does it work on my phone?',
    a: 'Yes. The site works on iPhone and Android. Tap the upload area to choose a photo or video from your camera roll.',
  },
]

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(null)

  const toggle = (i) => {
    setOpenIndex(openIndex === i ? null : i)
  }

  return (
    <div className="mt-10">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Common questions</h3>
      <div className="space-y-2">
        {QUESTIONS.map((item, i) => {
          const isOpen = openIndex === i
          return (
            <div key={i} className="border border-gray-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggle(i)}
                className="w-full flex items-center justify-between px-3 sm:px-5 py-4 text-left text-sm text-gray-300 hover:bg-gray-900/50 transition-colors"
                style={{ minHeight: '44px' }}
              >
                <span>{item.q}</span>
                <span className="text-gray-500 text-lg ml-3 flex-shrink-0 w-5 text-center">
                  {isOpen ? '\u2212' : '+'}
                </span>
              </button>
              <div
                className="overflow-hidden transition-all duration-300 ease-in-out"
                style={{ maxHeight: isOpen ? '200px' : '0px' }}
              >
                <p className="px-3 sm:px-5 pb-4 text-sm text-gray-500 leading-relaxed">
                  {item.a}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
