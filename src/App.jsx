import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Home } from './pages/Home';
import { NotFound } from './pages/NotFound';
import { Toaster } from '@/components/ui/toaster';
import { Admin } from './pages/Admin';

function App() {
  return (
    <>
    <Toaster />
    <BrowserRouter>
      <Routes>
        <Route index element={<Home />} />
        <Route path="/secret-admin-page" element={<Admin />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
    </>
  )
}

export default App
