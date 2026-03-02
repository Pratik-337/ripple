import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { authStore } from '../lib/authStore';

export function useRippleSocket() {
    const queryClient = useQueryClient();
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
    const backoffRef = useRef(1000);

    useEffect(() => {
        let unmounted = false;

        const connect = () => {
            const { user, accessToken } = authStore.getState();
            if (!user || !accessToken) return;

            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

            const metaEnv = (import.meta as any).env;
            const wsHost = metaEnv.VITE_API_URL
                ? new URL(metaEnv.VITE_API_URL).host
                : 'localhost:8000';
            const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws/${user.id}?token=${accessToken}`;

            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('[WebSocket] Connected');
                backoffRef.current = 1000;
            };

            ws.onmessage = (event) => {
                try {
                    const payload = JSON.parse(event.data);
                    if (payload.event === 'ping') return;

                    handleEvent(payload);
                } catch (err) {
                    console.error('[WebSocket] Failed to parse message', err);
                }
            };

            ws.onclose = (event) => {
                console.log('[WebSocket] Disconnected', event.code);
                wsRef.current = null;

                if (!unmounted && event.code !== 4001) {
                    // 4001 used manually for unauthorized close
                    const timeout = Math.min(backoffRef.current * 1.5, 30000);
                    backoffRef.current = timeout;
                    console.log(`[WebSocket] Reconnecting in ${timeout}ms...`);
                    reconnectTimeoutRef.current = setTimeout(connect, timeout);
                }
            };

            ws.onerror = (error) => {
                console.error('[WebSocket] Error', error);
            };

            wsRef.current = ws;
        };

        const handleEvent = (payload: any) => {
            const { event, data } = payload;
            console.log(`[WebSocket Event] ${event}`, data);

            switch (event) {
                case 'notification:new':
                    queryClient.invalidateQueries({ queryKey: ['notifications'] });
                    break;
                case 'invite:received':
                    queryClient.invalidateQueries({ queryKey: ['invites'] });
                    break;
                case 'project:files_ready':
                    queryClient.invalidateQueries({ queryKey: ['project', data.project_id] });
                    queryClient.invalidateQueries({ queryKey: ['projects'] });
                    break;
                case 'impact:parser_complete':
                case 'impact:llm_complete':
                case 'impact:llm_failed':
                    queryClient.invalidateQueries({ queryKey: ['changes', data.change_request_id, 'impact'] });
                    break;
                case 'change:acknowledged':
                case 'change:approved':
                case 'change:auto_confirmed':
                    queryClient.invalidateQueries({ queryKey: ['changes'] });
                    queryClient.invalidateQueries({ queryKey: ['project'] });
                    break;
                default:
                    break;
            }
        };

        connect();

        return () => {
            unmounted = true;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close(1000, 'Unmounting hooks');
            }
        };
    }, [queryClient]);
}
