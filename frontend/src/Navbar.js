import React from 'react'
import {BrowserRouter as Router, Routes, Route, Link} from "react-router-dom"
import Home from './Home';
import Pantry from './pantry';
import logo from './logo.svg';
import axios from 'axios';
import './Home.css';


require('dotenv').config()

export default function Navbar() {
  return (
    <Router>
    <div className="navbarHome">
        <nav>
            <button><Link to="/">Home</Link></button>
            <button><Link to="/purchase_history">Analyze Past Purchases</Link></button>
            <button><Link to="/pantrys">Explore Virtual Pantry</Link></button>
            <button><Link to="/promotions">See Current Promotions</Link></button>
            <button><Link to="/recipes">Find New Recipes</Link></button>
        </nav>
    </div>
    <Routes>
        <Route path="/recipes" element={<Pantry></Pantry>}></Route>
        <Route path="/promotions" element={<Pantry></Pantry>}></Route>
        <Route path="/pantrys" element={<Pantry></Pantry>}></Route>
        <Route path="/purchase_history" element={<Pantry></Pantry>}></Route>
        <Route path="/" element={<Home></Home>}></Route>
    </Routes>
    </Router>
  )
}
