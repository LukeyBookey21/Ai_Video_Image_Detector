/* Gallery — educational page showing examples of AI tells */
import React from 'react'

const EXAMPLES = [
  {
    category: 'Hands and fingers',
    description: 'AI frequently generates extra fingers, fused digits, or impossibly bent joints. Always check the hands first.',
    tells: ['Extra or missing fingers', 'Fingers merging into each other', 'Wrists that bend unnaturally', 'Rings that float or merge with skin'],
  },
  {
    category: 'Eyes and teeth',
    description: 'Look carefully at the eyes — AI sometimes generates different eye colours, mismatched iris sizes, or teeth that blur together.',
    tells: ['Mismatched eye colour or size', 'Teeth that blur or merge', 'Reflections in eyes that don\'t match', 'Pupils that aren\'t round'],
  },
  {
    category: 'Hair and ears',
    description: 'Hair strands at the boundary between face and background often show artifacts. Ears may be asymmetric or have impossible geometry.',
    tells: ['Hair that melts into the background', 'Earrings that differ between ears', 'Ears with different shapes', 'Hair that passes through objects'],
  },
  {
    category: 'Background details',
    description: 'AI struggles with coherent backgrounds. Text is often garbled, architecture can be impossible, and objects may not follow physical rules.',
    tells: ['Garbled or nonsensical text on signs', 'Windows and doors that don\'t align', 'Objects that fade or morph', 'Impossible architecture'],
  },
  {
    category: 'Skin and texture',
    description: 'AI-generated faces tend to have unnaturally smooth skin, especially when you zoom in. Real skin has pores, fine lines, and imperfections.',
    tells: ['Plastic-looking skin with no pores', 'Inconsistent skin texture across the face', 'Smooth necks with no wrinkles', 'Sharp boundary between face and neck'],
  },
  {
    category: 'Symmetry',
    description: 'AI sometimes makes faces too symmetric. Real faces are naturally asymmetric — slightly different eye heights, uneven nostrils, etc.',
    tells: ['Perfectly symmetric features', 'Both sides of face looking identical', 'Jewellery perfectly mirrored', 'Hair parting that\'s too perfect'],
  },
]

export default function Gallery() {
  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300 mb-6 block">Back to detector</a>
        <h1 className="text-2xl font-bold text-white mb-2">What to look for in AI images</h1>
        <p className="text-sm text-gray-500 mb-8">Learn the common telltale signs of AI-generated content so you can spot them without any tools.</p>

        <div className="space-y-6">
          {EXAMPLES.map((ex, i) => (
            <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
              <h2 className="text-base font-semibold text-indigo-400 mb-2">{ex.category}</h2>
              <p className="text-sm text-gray-400 mb-3">{ex.description}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {ex.tells.map((tell, j) => (
                  <div key={j} className="flex items-start gap-2 text-xs text-gray-500">
                    <span className="text-indigo-400 mt-0.5 shrink-0">&#x2022;</span>
                    <span>{tell}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 p-5 bg-yellow-900/10 border border-yellow-800/30 rounded-xl">
          <p className="text-sm text-yellow-400 font-medium mb-2">Remember</p>
          <p className="text-xs text-gray-400">
            AI generators are improving rapidly. These tells work for most current AI images, but the latest models may avoid some of them.
            When in doubt, use our detector tool alongside your own observation.
          </p>
        </div>
      </div>
    </div>
  )
}
