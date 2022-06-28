import React from 'react'
import {BrowserRouter as Router, Routes, Route, Link} from "react-router-dom"
import Home from './Home';
import Pantry from './pantry';
import Constuction from './construction';
import Trips from './trips';
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
            <button><Link to="/trips">Trips</Link></button>
            <button><Link to="/stores">Stores</Link></button>
            <button><Link to="/promotions">Promotions</Link></button>
            <button><Link to="/pantry">Pantry</Link></button>
            <button><Link to="/recipes">Recipes</Link></button>
            <button><Link to="/mealplan">Meal Plans</Link></button>
        </nav>
    </div>
    <Routes>
        <Route path="/trips" element={<Trips></Trips>}></Route>
        <Route path="/pantry" element={<Pantry></Pantry>}></Route>
        <Route path="/promotions" element={<Constuction></Constuction>}></Route>
        <Route path="/stores" element={<Constuction></Constuction>}></Route>
        <Route path="/recipes" element={<Constuction></Constuction>}></Route>
        <Route path="/mealplan" element={<Constuction></Constuction>}></Route>
        <Route path="/" element={<Home></Home>}></Route>
    </Routes>
    </Router>
  )
}
