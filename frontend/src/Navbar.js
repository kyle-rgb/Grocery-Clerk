import React from 'react'

export default function Navbar() {
  return (
    <div class="navbarHome">
        <nav>
            <button><a href="/purchase_history">Analyze Past Purchases</a></button>
            <button><a href="/pantry">Explore Virtual Pantry</a></button>
            <button><a href="/promotions">See Current Promotions</a></button>
        </nav>
    </div>
  )
}
