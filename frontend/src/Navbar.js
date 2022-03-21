import React from 'react'

export default function Navbar() {
  return (
    <div className="navbarHome">
        <nav>
            <button><a href="/purchase_history">Analyze Past Purchases</a></button>
            <button><a href="/pantry">Explore Virtual Pantry</a></button>
            <button><a href="/promotions">See Current Promotions</a></button>
            <button><a href="/recipes">Find New Recipes</a></button>
        </nav>
    </div>
  )
}
