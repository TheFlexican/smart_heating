import { useEffect, useRef, useState } from 'react'
import { Zone } from '../types'

interface WebSocketMessage {
  type: string
  id?: number
  data?: {
    areas?: Zone[]
    area?: Zone
    area_id?: string
  }
  error?: {
    code: string
    message: string
  }
  success?: boolean
  result?: any
  ha_version?: string
}

interface UseWebSocketOptions {
  onZonesUpdate?: (areas: Zone[]) => void
  onZoneUpdate?: (area: Zone) => void
  onZoneDelete?: (areaId: string) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const messageIdRef = useRef(1)
  const isAuthenticatedRef = useRef(false)

  const getAuthToken = (): string | null => {
    // Try to get auth token from localStorage (HA stores it there)
    const haTokens = localStorage.getItem('hassTokens')
    if (haTokens) {
      try {
        const tokens = JSON.parse(haTokens)
        return tokens.access_token
      } catch (e) {
        console.error('Failed to parse HA tokens:', e)
      }
    }
    return null
  }

  const connect = () => {
    try {
      // Get WebSocket URL from current location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/websocket`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws
      isAuthenticatedRef.current = false

      ws.onopen = () => {
        // WebSocket connection opened, waiting for authentication
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // Handle authentication phase
          if (message.type === 'auth_required') {
            const token = getAuthToken()
            if (!token) {
              console.warn('No auth token found - WebSocket real-time updates will be disabled')
              setError('No authentication token available')
              setIsConnected(false)
              ws.close()
              // Don't try to reconnect if there's no token
              reconnectAttempts.current = maxReconnectAttempts
              return
            }
            
            ws.send(JSON.stringify({
              type: 'auth',
              access_token: token
            }))
            return
          }
          
          if (message.type === 'auth_ok') {
            isAuthenticatedRef.current = true
            setIsConnected(true)
            setError(null)
            reconnectAttempts.current = 0
            options.onConnect?.()
            
            // Now subscribe to our custom events
            ws.send(JSON.stringify({
              id: messageIdRef.current++,
              type: 'smart_heating/subscribe'
            }))
            return
          }
          
          if (message.type === 'auth_invalid') {
            console.error('Authentication failed:', message.error)
            setError('Authentication failed')
            ws.close()
            return
          }
          
          // Handle command phase messages
          if (message.type === 'result') {
            // Check if this is a subscription update (has event data)
            if (message.result?.event === 'update' && message.result?.data?.areas) {
              // Convert areas object to array (backend sends object with area_id as keys)
              const areasData = message.result.data.areas
              const areasArray = Object.values(areasData) as Zone[]
              options.onZonesUpdate?.(areasArray)
              return
            }
            
            if (!message.success) {
              console.error('Command failed:', message.error)
              setError(message.error?.message || 'Command failed')
            }
            return
          }
          
          if (message.type === 'event') {
            // Handle our custom area events
            const event = message.result || message
            if (event.data?.areas) {
              options.onZonesUpdate?.(event.data.areas)
            } else if (event.data?.area) {
              options.onZoneUpdate?.(event.data.area)
            } else if (event.data?.area_id) {
              options.onZoneDelete?.(event.data.area_id)
            }
            return
          }
          
          // Legacy message handling (for backward compatibility)
          switch (message.type) {
            case 'areas_updated':
              if (message.data?.areas) {
                options.onZonesUpdate?.(message.data.areas)
              }
              break
            
            case 'area_updated':
              if (message.data?.area) {
                options.onZoneUpdate?.(message.data.area)
              }
              break
            
            case 'area_deleted':
              if (message.data?.area_id) {
                options.onZoneDelete?.(message.data.area_id)
              }
              break
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('WebSocket connection error')
        options.onError?.('Connection error')
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
        options.onDisconnect?.()

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        } else {
          setError('Failed to connect after multiple attempts')
          options.onError?.('Connection failed')
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
  }

  const send = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
      return true
    }
    return false
  }

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [])

  return {
    isConnected,
    error,
    send,
    reconnect: connect,
  }
}
