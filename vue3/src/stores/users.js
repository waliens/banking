import { defineStore } from "pinia";
import UserService from "../data/services/user_service";

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: null
  }),
  actions: {
    async init() {
      await this.update_users();
    },
    async update_users() {
      if (!this.users) {
        const user_service = new UserService();
        this.users = await user_service.fetch_all();
      }
    },
    async add_user(user) {
      if (!this.users) {
        this.users = [user];
      } else {
        this.users.push(user);
      }
    },
    async update_user(user) {
      const index = this.users.findIndex(u => u.id == user.id);
      if (index < 0) {
        throw new Error(`User with id ${user.id} not found.`);
      }
      this.users[index] = user;
    }
  },
  getters: {
    get_user_by_id: (state) => (id) => {
      return state.users.find(user => user.id == id);
    },
  }
})