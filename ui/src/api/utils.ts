import {
    dependencyMap, isDependencyAffected,
    objectIdToPrimitive,
    objectIdToString,
    ObjID,
    primitiveObjectIdToString
} from "@/api/model/modelBase";

export const NameStatus = {
    NAME_INVALID: 1,
    NAME_TAKEN: 2,
    NAME_AVAILABLE: 3,
}

export type StateUpdateMessage = {
    update_type: string,
    identifier: ObjID,
    changes: {[key: string]: any} | null,
};

export class SocketConnection {

    connected: boolean
    queue: any[]
    sock?: WebSocket
    sock_delay: number = 1
    sessionId: string

    constructor(sessionId: string) {
        this.connected = false;
        this.queue = [];
        this.sessionId = sessionId;
        this.try_connect();
    }

    async confirm(msgId: number) {
        const message = {
            type: 'ConfirmEvent',
            data: {
                confirm_message_id: msgId,
                payload: {},
            }
        }
        this.sock?.send(JSON.stringify(message));
    }

    async onWsMessage(event: MessageEvent) {

        const data: {type: string, data: {[key: string]: any}, msg_id: number} = JSON.parse(event.data);

        if (data.type == 'ModelUpdateEvent') {
            const payload: StateUpdateMessage = data.data as StateUpdateMessage;
            const idStr = primitiveObjectIdToString(objectIdToPrimitive(payload.identifier));

            console.log("Updated ID", idStr, "Type", payload.update_type, "Changes", payload.changes);

            // find all objects that depend on updated key.
            // we need to keep in mind that there may not be exact matches.
            // models that depend on entire table need to be updated when any row is updated.

            let dependencies = dependencyMap[idStr] || [];

            if (payload.identifier.obj_id != null) {
                const idStrNoObj = primitiveObjectIdToString({
                    entity: payload.identifier.entity,
                    obj_id: null,
                });
                // update for any row should also trigger update for entire table
                dependencies = dependencies.concat(dependencyMap[idStrNoObj] || []);
            }

            dependencies.forEach(([dep, model]) => {
                // only update model if there is no advanced dependency declared,
                // or if update matches declared dependency
                if (!dep || isDependencyAffected(dep, model, payload)) {
                    console.log("Model will be updated", model)
                    model.initiateRefresh();
                }
            });

            await this.confirm(data.msg_id);
        }
    }

    onOpen() {
        if (!this.sock)
            return;

        const sock = this.sock as WebSocket;

        console.log("Socket opened");
        this.sock_delay = 1;
        this.connected = true;
        this.queue.forEach(packet => {
            sock.send(JSON.stringify(packet));
        });
        this.queue = [];
    }

    onClose() {
        console.log(`socket closed, trying to reconnect after ${this.sock_delay} seconds`);
        this.sock = undefined;

        const reconnectFunc = ()=>this.try_connect();

        setTimeout(
            reconnectFunc,
            this.sock_delay * 1000
        );

        this.sock_delay = Math.min(this.sock_delay + 5, 30);
    }

    try_connect() {

        this.sock = new WebSocket("ws://" + window.location.hostname + ":8000/ws/connect?session_id=" + this.sessionId);

        this.sock.onmessage = event => this.onWsMessage(event);
        this.sock.onopen = this.onOpen
        this.sock.onclose = () => this.onClose();
    }
}

export async function playMatchFound() {
    const audio = new Audio('/old-match-found.mp3');
    try {
        audio.volume = 0.5;
        await audio.play();
    } catch (e) {
        console.log("Failed to play sound", e);
    }
}

export function formatDateAsDelta(date: string) {
    if (!date) {
        return "never";
    }

    const now = new Date();
    const then = new Date(date);

    const delta = now.getTime() - then.getTime();

    const seconds = Math.floor(delta / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);

    if (years > 0) {
        return `${years} years ago`;
    }
    else if (months > 0) {
        return `${months} months ago`;
    }
    else if (weeks > 0) {
        return `${weeks} weeks ago`;
    }
    else if (days > 0) {
        return `${days} days ago`;
    }
    else if (hours > 0) {
        return `${hours} hours ago`;
    } else if (minutes > 0) {
        return `${minutes} minutes ago`;
    } else {
        return `${seconds} seconds ago`;
    }
}

export function formatDate(date: string) {
    if (!date) {
        return "never";
    }

    const d = new Date(date);
    return d.toLocaleString();
}

export async function copyToClipboard(textToCopy: string) {
    // Navigator clipboard api needs a secure context (https)
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(textToCopy);
    } else {
        // Use the 'out of viewport hidden text area' trick
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;

        // Move textarea out of the viewport so it's not visible
        textArea.style.position = "absolute";
        textArea.style.left = "-999999px";

        document.body.prepend(textArea);
        textArea.select();

        try {
            document.execCommand('copy');
        } catch (error) {
            console.error(error);
        } finally {
            textArea.remove();
        }
    }
}