import { useState, useEffect } from 'react'

export default function Typewriter({ phrases, typeSpeed = 45, deleteSpeed = 25, pauseTime = 1800 }) {
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [text, setText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const currentPhrase = phrases[phraseIndex]

    if (!isDeleting && text === currentPhrase) {
      const pause = setTimeout(() => setIsDeleting(true), pauseTime)
      return () => clearTimeout(pause)
    }

    if (isDeleting && text === '') {
      setIsDeleting(false)
      setPhraseIndex((prev) => (prev + 1) % phrases.length)
      return
    }

    const speed = isDeleting ? deleteSpeed : typeSpeed
    const timeout = setTimeout(() => {
      setText((prev) =>
        isDeleting ? currentPhrase.slice(0, prev.length - 1) : currentPhrase.slice(0, prev.length + 1)
      )
    }, speed)

    return () => clearTimeout(timeout)
  }, [text, isDeleting, phraseIndex, phrases, typeSpeed, deleteSpeed, pauseTime])

  return (
    <span className="typewriter-text">
      {text}
      <span className="typewriter-cursor">|</span>
    </span>
  )
}
