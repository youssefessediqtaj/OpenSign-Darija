import { create } from 'zustand';

type MessageStore = {
  currentMessageId: string | null;
  setCurrentMessageId: (id: string | null) => void;
};

export const useMessageStore = create<MessageStore>((set) => ({
  currentMessageId: null,
  setCurrentMessageId: (id) => set({ currentMessageId: id }),
}));
