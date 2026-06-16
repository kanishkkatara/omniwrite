import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { BrandProfile, BrandProfileCreate, BrandProfileUpdate } from "@/types/brand";
import * as api from "@/lib/api";

interface BrandState {
  brands: BrandProfile[];
  activeBrandId: string | null;
  isLoading: boolean;
  error: string | null;
  isWizardOpen: boolean;
}

interface BrandActions {
  fetchBrands: () => Promise<void>;
  setActiveBrand: (id: string | null) => void;
  createBrand: (data: BrandProfileCreate) => Promise<BrandProfile>;
  updateBrand: (id: string, data: BrandProfileUpdate) => Promise<BrandProfile>;
  deleteBrand: (id: string) => Promise<void>;
  getActiveBrand: () => BrandProfile | null;
  setIsWizardOpen: (open: boolean) => void;
}

type BrandStore = BrandState & BrandActions;

export const useBrandStore = create<BrandStore>()(
  persist(
    (set, get) => ({
      brands: [],
      activeBrandId: null,
      isLoading: false,
      error: null,
      isWizardOpen: false,

      fetchBrands: async () => {
        set({ isLoading: true, error: null });
        try {
          const brands = await api.getBrands();
          set({ brands, isLoading: false });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "Failed to fetch brands",
            isLoading: false,
          });
        }
      },

      setActiveBrand: (id) => {
        set({ activeBrandId: id });
      },

      createBrand: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const brand = await api.createBrand(data);
          set((state) => ({
            brands: [...state.brands, brand],
            activeBrandId: brand.id,
            isLoading: false,
          }));
          return brand;
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "Failed to create brand",
            isLoading: false,
          });
          throw err;
        }
      },

      updateBrand: async (id, data) => {
        set({ isLoading: true, error: null });
        try {
          const updated = await api.updateBrand(id, data);
          set((state) => ({
            brands: state.brands.map((b) => (b.id === id ? updated : b)),
            isLoading: false,
          }));
          return updated;
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "Failed to update brand",
            isLoading: false,
          });
          throw err;
        }
      },

      deleteBrand: async (id) => {
        set({ isLoading: true, error: null });
        try {
          await api.deleteBrand(id);
          set((state) => ({
            brands: state.brands.filter((b) => b.id !== id),
            activeBrandId:
              state.activeBrandId === id ? null : state.activeBrandId,
            isLoading: false,
          }));
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "Failed to delete brand",
            isLoading: false,
          });
          throw err;
        }
      },

      getActiveBrand: () => {
        const { brands, activeBrandId } = get();
        return brands.find((b) => b.id === activeBrandId) ?? null;
      },

      setIsWizardOpen: (open) => {
        set({ isWizardOpen: open });
      },
    }),
    {
      name: "brand-store",
      partialize: (state) => ({ activeBrandId: state.activeBrandId }),
    }
  )
);
