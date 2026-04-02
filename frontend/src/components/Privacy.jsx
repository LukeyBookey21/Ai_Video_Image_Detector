/* Privacy — privacy policy page */
import React from 'react'

export default function Privacy() {
  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300 mb-6 block">Back to detector</a>
        <h1 className="text-2xl font-bold text-white mb-8">Privacy Policy</h1>
        <div className="space-y-6 text-sm text-gray-400 leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Your files</h2>
            <p>When you upload a file for analysis, it is processed in memory on our server and deleted immediately after the analysis is complete. We never store, save, log, or share your uploaded images or videos. Video files are saved temporarily to disk during processing and deleted as soon as analysis finishes, even if an error occurs.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">URL analysis</h2>
            <p>When you submit a URL, we download the file from that URL to a temporary location, analyse it, and delete it immediately. We do not store the URL or the downloaded content. We do not access any page other than the specific URL you provide.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Analysis history</h2>
            <p>Your recent analysis history is stored locally in your browser using localStorage. This data never leaves your device. We have no access to it. You can clear it at any time using the "Clear history" button.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Email waitlist</h2>
            <p>If you join the waitlist, your email address is stored in a local CSV file on the server. Your IP address is hashed (one-way, irreversible) and stored alongside it for abuse prevention. We will never sell or share your email address.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Analytics</h2>
            <p>We count the total number of analyses performed (how many images checked, how many flagged as AI). These counters contain no personal information — just numbers. No cookies, no tracking pixels, no third-party analytics.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Security</h2>
            <p>All uploaded files are validated for type and size before processing. We use rate limiting to prevent abuse. File names from uploads are never used on our filesystem — temporary files use random identifiers.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Contact</h2>
            <p>If you have questions about this policy, please open an issue on our GitHub repository.</p>
          </section>
        </div>
      </div>
    </div>
  )
}
