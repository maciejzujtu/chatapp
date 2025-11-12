"use client"
import { Dispatch, SetStateAction, useEffect, useState } from "react"
import { WebsocketListener } from "../api/server"

function send_message(content: string, ws: WebSocket, setMessage: Dispatch<SetStateAction<string>>) {
    ws.send(content)
    setMessage("")
}

const ws = new WebsocketListener()
const server = ws.server

export default function Chatroom() {
    const [message, setMessage] = useState("")
    const [messages, setMessages] = useState<string[]>([])

    // Listen for messages from server
    useEffect(() => {
        server.addEventListener("message", (msg) => {
            setMessages((prev) => [...prev, msg.data])
        })
    }, [])

    return (
        <div>
            <h2>Chatroom</h2>
            <input  
                type="text" 
                placeholder="Type something"
                className="bg-white text-black w-1/2"
                onChange={(e) => setMessage(e.target.value)}
                value={message}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && message.trim() !== "") {
                        send_message(message, server, setMessage)
                    }
                }}
            />
            
            <h1>Messages</h1>
            <div 
                id="messages"
                className="bg-white text-black w-1/2 h-80 overflow-auto p-2"
            >
                {messages.map((m, index) => (
                    <div className="text-black" key={index}>{m}</div>
                ))}
            </div>
        </div>
    )
}