import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { StatusBadge } from './StatusBadge';
import type { AlertItem } from '../../types';

interface AlertAcknowledgedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onViewIncidents: () => void;
  alert: AlertItem | null;
}

const formatTime = (iso?: string) =>
  iso ? new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—';

/**
 * Success-state confirmation for the "Acknowledge alert" action (see
 * DashboardPage's handleAck). Same two-panel confirmation pattern as a
 * standard checkout/timesheet success modal — a spring-in checkmark and
 * headline on the left, an audit-trail summary of what actually changed
 * on the right — restyled to match the app theme and re-keyed to real alert fields
 * instead of invented data (no functionality change: this only presents
 * the result of the existing acknowledgeAlert() call already made by the
 * caller before opening the modal).
 */
export function AlertAcknowledgedModal({ isOpen, onClose, onViewIncidents, alert }: AlertAcknowledgedModalProps) {
  return (
    <AnimatePresence>
      {isOpen && alert && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#18243A]/45 p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.95, y: 20, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="relative w-full max-w-3xl overflow-hidden rounded-[24px] border border-[#E9EDF2] bg-white shadow-[0_0_0_1px_rgba(4,23,43,0.05),0_20px_60px_rgba(0,0,0,0.12)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="grid grid-cols-1 md:grid-cols-2">
              {/* Left: confirmation */}
              <div className="flex flex-col items-center justify-center gap-4 p-10 text-center bg-[#F1F5F9]">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1, transition: { delay: 0.15, type: 'spring', stiffness: 220, damping: 16 } }}
                >
                  <CheckCircle2 className="h-14 w-14 text-[#15803d]" />
                </motion.div>
                <h2 className="font-[family-name:var(--font-signifier)] text-2xl leading-tight text-[#18243A]">
                  Alert acknowledged
                </h2>
                <p className="text-sm text-[#6F7F98] max-w-xs">
                  The alert has been logged as acknowledged and removed from the open queue. Evidence and
                  timeline history remain intact for review.
                </p>
                <div className="mt-2 flex w-full max-w-xs flex-col gap-2">
                  <Button onClick={onClose}>Done</Button>
                  <Button variant="ghost" onClick={onViewIncidents}>
                    Open incident board
                  </Button>
                </div>
              </div>

              {/* Right: summary */}
              <div className="relative p-8">
                <button
                  type="button"
                  aria-label="Close"
                  onClick={onClose}
                  className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-full text-[#6F7F98] hover:bg-[#F1F5F9] hover:text-[#18243A] transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
                <h3 className="font-[family-name:var(--font-signifier)] font-bold text-lg text-[#18243A] mb-6">
                  Acknowledgement summary
                </h3>

                <div className="space-y-4 text-sm">
                  <div>
                    <p className="text-[#6F7F98]">Alert message</p>
                    <p className="font-medium text-[#18243A]">{alert.message}</p>
                  </div>
                  <div>
                    <p className="text-[#6F7F98]">Zone</p>
                    <p className="font-medium text-[#18243A]">{alert.zone_id ?? 'Zone unavailable'}</p>
                  </div>
                </div>

                <Separator className="my-6" />

                <div className="space-y-3 text-sm">
                  <motion.div
                    className="flex justify-between items-center"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0, transition: { delay: 0.3 } }}
                  >
                    <p className="text-[#6F7F98]">Logged at</p>
                    <p>{formatTime(alert.created_at)}</p>
                  </motion.div>
                  <motion.div
                    className="flex justify-between items-center"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0, transition: { delay: 0.4 } }}
                  >
                    <p className="text-[#6F7F98]">Acknowledged at</p>
                    <p>{formatTime(alert.acknowledged_at ?? new Date().toISOString())}</p>
                  </motion.div>
                  <motion.div
                    className="flex justify-between items-center"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0, transition: { delay: 0.5 } }}
                  >
                    <p className="text-[#6F7F98]">Deduplication key</p>
                    <p className="text-xs text-[#9DAFC5]">{alert.deduplication_key}</p>
                  </motion.div>
                </div>

                <Separator className="my-6" />

                <motion.div
                  className="flex items-center justify-between rounded-2xl bg-[#EAF0FF] px-4 py-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1, transition: { delay: 0.6 } }}
                >
                  <p className="font-medium text-[#2F52D6]">Severity at acknowledgement</p>
                  <StatusBadge level={alert.alert_level} size="md" />
                </motion.div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
