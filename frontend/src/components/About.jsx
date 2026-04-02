/* About — explains how the detector works in plain English */
import React from 'react'

export default function About() {
  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300 mb-6 block">Back to detector</a>
        <h1 className="text-2xl font-bold text-white mb-8">How it works</h1>
        <div className="space-y-6 text-sm text-gray-400 leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">What this tool does</h2>
            <p>This tool checks whether an image or video was created by AI (like Midjourney, Stable Diffusion, or DALL-E) or is a genuine photograph/recording. It uses multiple independent checks and combines them into a single verdict.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">How we check</h2>
            <p className="mb-3">We run 9 or more independent checks on every file. Here are the main ones:</p>
            <ul className="space-y-3">
              <li className="pl-4 border-l-2 border-indigo-500/30">
                <strong className="text-gray-300">File origin check</strong> — Real camera photos contain metadata: camera model, settings, date, sometimes GPS. AI images almost never have this. This is our strongest signal.
              </li>
              <li className="pl-4 border-l-2 border-indigo-500/30">
                <strong className="text-gray-300">Hidden frequency patterns</strong> — Every image has patterns invisible to the human eye. Real photos follow natural mathematical rules (called "1/f noise"). AI images often break these rules in subtle ways.
              </li>
              <li className="pl-4 border-l-2 border-indigo-500/30">
                <strong className="text-gray-300">Noise fingerprinting</strong> — Camera sensors add tiny amounts of random noise. This noise has a specific character depending on the camera. AI generators produce different noise patterns.
              </li>
              <li className="pl-4 border-l-2 border-indigo-500/30">
                <strong className="text-gray-300">Texture and edge analysis</strong> — Real photos have natural texture variation. AI images can be too smooth or have unnatural edges, especially in fine details.
              </li>
              <li className="pl-4 border-l-2 border-indigo-500/30">
                <strong className="text-gray-300">Face analysis</strong> — If faces are found, we check for symmetry, skin texture, and boundary artifacts. AI-generated faces often have subtle abnormalities.
              </li>
              <li className="pl-4 border-l-2 border-indigo-500/30">
                <strong className="text-gray-300">Colour space forensics</strong> — We analyse colour relationships in ways the eye can't see. AI generators handle colour differently from real cameras.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">For videos</h2>
            <p>We extract 15 frames from the video and check each one individually. We also analyse how frames relate to each other — looking for flicker, inconsistent motion, and unnatural transitions that deepfake generators produce.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">What it can't do</h2>
            <ul className="space-y-2">
              <li>It cannot detect edited photos (Photoshop, filters) — only fully AI-generated content</li>
              <li>Heavy compression (WhatsApp, Instagram) removes some of the signals we check</li>
              <li>Screenshots lose all camera metadata, making detection harder</li>
              <li>The latest AI generators keep improving, so no tool is 100% accurate</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-200 mb-2">Our accuracy</h2>
            <p>On our test set of real camera photos vs AI-generated images, we achieve 92% accuracy with zero false positives (real photos never incorrectly flagged as AI). With ML models enabled, accuracy improves further.</p>
          </section>
        </div>
      </div>
    </div>
  )
}
