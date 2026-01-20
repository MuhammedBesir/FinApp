/**
 * 404 Not Found Page
 */
import React from "react";
import { Link } from "react-router-dom";
import { Home, ArrowLeft, Search } from "lucide-react";

const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative text-center max-w-md">
        {/* 404 Number */}
        <div className="mb-8">
          <h1 className="text-[150px] font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-400 via-accent-400 to-primary-400 leading-none">
            404
          </h1>
        </div>

        {/* Message */}
        <h2 className="text-2xl font-bold text-white mb-4">
          Sayfa Bulunamadı
        </h2>
        <p className="text-slate-400 mb-8">
          Aradığınız sayfa mevcut değil veya taşınmış olabilir. 
          Ana sayfaya dönerek devam edebilirsiniz.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 transition-all"
          >
            <Home className="w-5 h-5" />
            Ana Sayfa
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white/5 border border-white/10 text-white rounded-xl hover:bg-white/10 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Geri Dön
          </button>
        </div>

        {/* Quick Links */}
        <div className="mt-12 pt-8 border-t border-white/10">
          <p className="text-sm text-slate-500 mb-4">Popüler Sayfalar</p>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              { label: "Dashboard", path: "/" },
              { label: "Sinyaller", path: "/signals" },
              { label: "Portföy", path: "/portfolio" },
              { label: "Halka Arz", path: "/ipo" },
            ].map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
