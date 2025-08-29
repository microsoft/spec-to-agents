import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import { Toaster } from 'sonner'
import { Navigation } from './components/Navigation'
import { EventPlanningDemo } from './components/EventPlanningDemo'
import { SpecsToAgentsCreator } from './components/SpecsToAgentsCreator'
import { LearningProgression } from './components/LearningProgression'
import './App.css'

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <Router>
        <div className="min-h-screen bg-background text-foreground">
          <Navigation />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<EventPlanningDemo />} />
              <Route path="/learning" element={<LearningProgression />} />
              <Route path="/specs-to-agents" element={<SpecsToAgentsCreator />} />
            </Routes>
          </main>
          <Toaster />
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App
