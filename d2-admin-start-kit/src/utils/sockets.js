// src/utils/socket.js
export class ChatSocket {
  constructor (url) {
    this.socket = null
    this.url = url
    this.messageQueue = []
    this.isConnected = false
  }

  connect () {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(this.url)

      this.socket.onopen = () => {
        this.isConnected = true
        resolve()
      }

      this.socket.onerror = (error) => {
        reject(error)
      }
    })
  }

  send (question) {
    if (!this.isConnected) {
      throw new Error('WebSocket 未连接')
    }
    this.socket.send(JSON.stringify({ question }))
  }

  onMessage (callback) {
    this.socket.onmessage = (event) => {
      callback(event.data)
    }
  }

  close () {
    this.socket.close()
    this.isConnected = false
  }
}
